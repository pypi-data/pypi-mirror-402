###############################################################################
#
#                                ACBICI   v2.1.0
#
#
#     Copyright (C) 2025 Fundación IMDEA Materiales (IMDEA Materials Institute), Getafe, Madrid, Spain and
#                        Universidad Politécnica de Madrid (UPM), Madrid, Spain
#     Contact: christina.schenk@imdea.org, ignacio.romero@imdea.org
#     Author: Christina Schenk, Ignacio Romero (christina.schenk@imdea.org, ignacio.romero@imdea.org)
#
#     This file is part of ACBICI.
#
#     # All rights reserved.
#
# ACBICI is licensed under the BSD 3-Clause License.
# You may use, redistribute, and modify this file under the terms of that license.
# See the LICENSE file in the repository root for full details.
#
# THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
#
###############################################################################

"""
Created on Fri Feb 17 16:09:02 2023

@author: Ignacio Romero, Christina Schenk
"""

import matplotlib.pyplot as plt
import math
from scipy.stats import multivariate_normal
from scipy.stats import norm
from pyDOE import lhs
import numpy as np
from numpy import linalg as LA
from numpy.linalg import inv
import random
import sys
from abc import ABC, abstractmethod


class randomProcess(ABC):
    """
    Abstract class for all the random processes employed for calibration in ACBICI.
    """


    @abstractmethod
    def covarianceMatrix_vect(self):
        """
        Calculate the covariance matrix.
        """
        pass


    @abstractmethod
    def eval_vect(self, Xstar):
        """
        Evaluate the random process at inputs Xstar

        Paramters
        ---------
        Xstar: a numpy array of input values. Each row is an input

        Returns
        -------
        A numpy vector of evaluations.
        """
        pass


    @abstractmethod
    def print(self):
        pass


# -----------------------------------------------------------------------------
#                        Type B problem: expensive model GP
# -----------------------------------------------------------------------------
class expensiveGaussianProcess(randomProcess):
    """
    Gaussian processes that have the structure of
    x ~ (GP of metamodel) + (experimental error)

    Reference: M.C. Kennedy and A. O'Hagan (2001): Bayesian calibration of computer models,
    J.R. Statist. Soc. B (2001), 63, Part 3 , pp. 425-464.
    """

    def __init__(self,
                 xExperimental, yExperimental,
                 xSynthetic, tSynthetic, ySynthetic, calibrator):
        """
        Constructor of KOH GP
            Gaussian process with the special structure of KOH
        It includes three terms:
           etahat(x, t) + delta(x) + epsilon(x)

        etahat: GP surrogate for the model. Depends on points and parameters
        delta: GP for the discrepancy error
        epsilon: the experimental error ~ N(0, sd_meas^2)

        Parameters
        ----------
        xExperimental: inputs x for experimental datapoints
        yExperimental: outputs for experimental datapoints (only scalars yet!)
        xSynthetic: inputs x for synthetic datapoints
        tSynthetic: parameter values for synthetic data datapoints
        ySynthetic: outputs for synthetic datapoints
        hyperparameters: parameters of the model + hyperparameters of GP
        model

        Returns
        -------
        KOH Gauss process object
        """
        self.xExp = xExperimental
        self.yExp = yExperimental
        self.nExp = len(xExperimental)

        self.xSyn = xSynthetic
        self.tSyn = tSynthetic
        self.ySyn = ySynthetic
        self.nSyn = len(xSynthetic)

        self.calibrator = calibrator


    def covarianceMatrix_vect(self):
        """
        Vectorized code
        Evaluate the covariance matrix with discrepancy when we fix the value of the
        experimental data, synthetic data, parameters theta and hyperparameters

        Parameters
        ----------
        ---

        Returns
        -------
          Sigma: covariance matrix
        """
        N = self.nExp
        M = self.nSyn

        Sigma = np.empty((N+M, N+M))
        x  = self.xExp
        xt = self.xSyn
        tt = self.tSyn

        theModel = self.calibrator.model
        thetax = np.tile(theModel.param, (N,1))
        covx = self.calibrator.covx
        covt = self.calibrator.covt
        s2 = self.calibrator.getExperimentalSTD()**2

        # Block 1,1 (shape NxN)
        Covx_1 = covx(x, x)
        Covt_1 = covt(thetax, thetax)
        Sigma[:N, :N] = Covx_1 * Covt_1

        # Ensure diagonal of Sigma[:N, :N] has s2 added
        np.fill_diagonal(Sigma[:N, :N], np.diag(Sigma[:N, :N]) + s2)

        # Block 1,2 (shape NxM)
        Covx_12 = covx(x, xt)
        Covt_12 = covt(thetax, tt)
        Sigma[:N, N:N + M] = Covx_12*Covt_12

        # Block 2,1 (shape MxN)
        Sigma[N:N + M, :N] = Sigma[:N, N:N + M].T

        # Block 2,2 (shape MxM)
        Covx_2 = covx(xt, xt)
        Covt_2 = covt(tt, tt)
        Sigma[N:N + M, N:N + M] = Covx_2 * Covt_2

        return Sigma


    def eval_vect(self, Xstar):
        """
        Vectorized code
        Evaluate mean and std of the GP at points Xstar. The parameters theta
        and the hyperparameters have been set before.

        Parameters
        ----------
        Xstar: array of input points where we want to evaluate the GP
               The 2nd dimension should be equal to the dimension of the
               input variables x

        Returns
        -------
        ystar: mean at every point of Xstar
        np.sqrt(diag): Sqrt of the diagonal of the covariance matrix

        """
        N = self.nExp
        M = self.nSyn

        theModel = self.calibrator.model
        thetax = np.tile(theModel.param, (N,1))
        covx = self.calibrator.covx
        covt = self.calibrator.covt
        s2 = self.calibrator.getExperimentalSTD()**2

        x = self.xExp
        xt = self.xSyn
        tt = self.tSyn

        xst = Xstar
        Nstar = len(Xstar)

        thetast = np.tile(theModel.param, (Nstar, 1))

        # covariance matrix at (e)xisting data, not Xstar
        Kee = self.covarianceMatrix_vect()
        Kee = Kee + np.diag(np.repeat(1e-8, N + M))

        #x-xstar block (shape N x Nstar)
        Covx_en = covx(x, xst)
        Covt_en = covt(thetax, thetast)
        Ken = np.zeros((N+M, Nstar))
        Ken[:N,:Nstar] = Covx_en*Covt_en

        #xtilde-xstar block (shape Ntilde x Nstar)
        Covxtxst_en = covx(xt, xst)
        Covttth_en = covt(tt, thetast)
        Ken[N:M+N,:Nstar] = Covxtxst_en*Covttth_en

        # xstar - xstar block (shape Nstar x Nstar)
        Knn = np.zeros((Nstar, Nstar))
        Covxstxst_nn = covx(xst, xst)
        Covtsttst_nn = covt(thetast, thetast)
        Knn[:Nstar, :Nstar] = Covxstxst_nn*Covtsttst_nn
        np.fill_diagonal(Knn[:Nstar, :Nstar], np.diag(Knn[:Nstar, :Nstar]) + s2)

        y = np.concatenate([self.yExp, self.ySyn])
        y = np.atleast_2d(y).T if self.calibrator.getOutputDimension() == 1 else np.atleast_2d(
            y)  # Convert y to a 2D array if it's not already
        L = np.linalg.cholesky(Kee)

        v = np.linalg.solve(L, y)
        u = np.linalg.solve(L.T, v)
        ystar = np.matmul(Ken.T, u)

        v = np.linalg.solve(L, Ken)
        K2 = np.matmul(v.T,v)

        Sigma = Knn - K2
        diag = np.diag(Sigma).copy()

        tol = 1e-8
        diag[np.abs(diag) < tol] = 0.0

        return ystar, np.sqrt(diag)


    def print(self):
        """ Print information about the GP for expensive model.

        Parameters
        ----------
        none

        Returns
        -------
        none
        """
        theModel = self.calibrator.model

        print("\n\nGaussian process object for expensive model")
        print("-----------------------------------------")
        print("   Number of of experimental data: ", self.nExp)
        print("   Number of synthetic data: ", self.nSyn)
        print("   Parameters")
        for i, label in enumerate(theModel.paramLabels):
            print("       {:8} = {:.5f}".format(label, theModel.param[i]));
        print("   Hyperparameters")
        for i, label in enumerate(self.calibrator.hyperLabels):
            print("       {:8} = {:.5f}".format(label, self.calibrator.hyper[i]));
        print("   Variance of experimental data: {0:.6f}".format(self.calibrator.expSTD**2))


# -----------------------------------------------------------------------------
#     Type C problem: random process with the structure of
#     (symbolic model) + (discrepancy GP) + (random noise gaussian)
# -----------------------------------------------------------------------------
class inexpKOHGaussianProcess():
    """
    Class for Kennedy O'Hagan calibration that involves an inexpensive model.
    """

    def __init__(self, xExperimental, yExperimental, calibrator):
        """
        Initilize KOH Gaussian process.

        Gaussian process with the special structure:

               eta(x, t) + delta(x) + epsilon(x)

        eta: a mathematical model. Depends on points-x and parameters-t
        delta: the discrepancy error (a GP)
        epsilon: the experimental error ~ N(0, noise^2)

        Parameters
        ----------
        xExperimental: input values for experimental datapoints
        yExperimental: measured values experimental datapoints
        model: core structure

        Returns
        -------
        inexpKOHGaussianProcess object
        """
        self.xExp = xExperimental
        self.yExp = yExperimental
        self.nExp = len(xExperimental)
        self.calibrator = calibrator


    def covarianceMatrix_vect(self):
        """
        Vectorized version
        Evaluate the covariance matrix for the inexpensive KOH model.

        Experimental data, parameters theta and hyperparameters are fixed.
        The matrix consists of the sum of the experimental (Gaussian) error
        and the discrepancy, if the model has the latter.

        Parameters
        ----------
        --

        Returns
        -------
        Sigma: covariance matrix
        """
        N = self.nExp
        s = self.calibrator.getExperimentalSTD()
        s2 = s*s

        Sigma = np.zeros((N,N))

        # Ensure diagonal of Sigma[:N, :N] has s2 added
        np.fill_diagonal(Sigma[:N, :N], np.diag(Sigma[:N, :N]) + s2)

        return Sigma


    def covarianceMatrix_vect_withdisc(self):
        """
        Vectorized version
        Evaluate the covariance matrix with discrepancy for the inexpensive KOH model.

        Experimental data, parameters theta and hyperparameters are fixed.
        The matrix consists of the sum of the experimental (Gaussian) error
        and the discrepancy, if the model has the latter.

        Parameters
        ----------
        --

        Returns
        -------
        Sigma: covariance matrix
        """
        N = self.nExp
        s = self.calibrator.getExperimentalSTD()
        s2 = s * s

        Sigma = np.zeros((N,N))
        x = self.xExp.view()
        covd = self.calibrator.covd

        Covd_1 = covd(x, x)  # shape (N, N)
        Sigma[:N, :N] = Covd_1

        # Ensure diagonal of Sigma[:N, :N] has s2 added
        np.fill_diagonal(Sigma[:N, :N], np.diag(Sigma[:N, :N]) + s2)

        return Sigma


        def transformed_model(xExp, mtheta):
            #num_tasks = self.model.getOutputDimension()
            # Evaluate the model
            output_matrix = self.model.original_symbolicModel(xExp, mtheta)  # Shape: (n * num_tasks, ydim)

            # Flatten the output to match the required shape
            reshaped_output = output_matrix.flatten().reshape(-1, 1)  # Shape: (n * num_tasks * ydim, 1)
            return reshaped_output

        theCore = self.calibrator.model
        self.original_symbolicModel = theCore.symbolicModel
        if self.calibrator.getOutputDimension()>1:
            self.symbolicModel = lambda xExp, mtheta: transformed_model(xExp, mtheta)

    def eval_vect(self, Xstar):
        """
        Vectorized code
        Evaluate mean and std of the GP at points Xstar.

        Parameters
        ----------
        Xstar: array of input points (npoints x dim)

        Returns
        -------
        ystar: mean vector
        std: standard deviation estimate for every evaluation point

        """
        x = self.xExp.view()
        y = self.yExp.view()
        y = np.atleast_2d(y).T if self.calibrator.getOutputDimension() == 1 else np.atleast_2d(y)  # Convert y to a 2D array if it's not already
        N = self.nExp

        xst = Xstar.view()
        Nstar = Xstar.shape[0]

        theCore = self.calibrator.model
        symbolic = theCore.symbolicModel

        Kee = self.covarianceMatrix_vect()
        Ken = np.zeros((N, Nstar))
        Knn = np.zeros((Nstar, Nstar))

        thetast = np.tile(theCore.param, (Nstar, 1))
        mun = symbolic(xst, thetast)

        thetax = np.tile(theCore.param, (N, 1))
        mue = symbolic(x, thetax)
        shift = y - mue

        L = np.linalg.cholesky(Kee)
        u = np.linalg.solve(L, shift)
        u = np.linalg.solve(np.transpose(L), u)
        ystar = mun + np.matmul(Ken.T, u)

        K2 = np.linalg.solve(L, Ken)
        K2 = np.matmul(K2.T, K2)
        Sigma = Knn - K2
        diag = np.diag(Sigma).copy()

        tol = 1e-8
        diag[np.abs(diag) < tol] = 0.0

        if np.min(diag) < 0.0:
            print("\n Singular diagonal:")
            sys.exit("Abort: Negative diagonal found")

        return ystar, np.sqrt(diag)


    def eval_vect_withdisc(self, Xstar):
        """
        Vectorized code
        Evaluate mean and std of the GP including discrepancy at points Xstar.

        Parameters
        ----------
        Xstar: array of input points

        Returns
        -------
        ystar: mean
        std: standard deviation estimate for every evaluation point

        """
        x = self.xExp.view()
        y = self.yExp.view()
        y = np.atleast_2d(y).T if self.calibrator.getOutputDimension() == 1 else np.atleast_2d(
            y)  # Convert y to a 2D array if it's not already
        N = self.nExp
        xst = Xstar.view()
        Nstar = Xstar.shape[0]
        ystar = np.zeros((Nstar,1))
        theCore = self.calibrator.model
        symbolic = theCore.symbolicModel
        covd = self.calibrator.covd

        Kee = self.covarianceMatrix_vect_withdisc()
        Ken = np.zeros((N, Nstar))
        Ken = covd(x, xst)

        Knn = np.zeros((Nstar, Nstar))
        Knn = covd(xst, xst)

        thetast = np.tile(theCore.param, (Nstar, 1))
        mun = symbolic(xst, thetast)

        thetax = np.tile(theCore.param, (N, 1))
        mue = symbolic(x, thetax)
        shift = y - mue

        L = np.linalg.cholesky(Kee)
        u = np.linalg.solve(L, shift)
        u = np.linalg.solve(np.transpose(L), u)
        ystar = mun + np.matmul(Ken.T, u)

        K2 = np.linalg.solve(L, Ken)
        K2 = np.matmul(K2.T, K2)
        Sigma = Knn - K2
        diag = np.diag(Sigma).copy()

        tol = 1e-8
        diag[np.abs(diag) < tol] = 0.0

        if np.min(diag) < 0.0:
            print("\n Singular diagonal:")
            sys.exit("Abort: Negative diagonal found")

        return ystar, np.sqrt(diag)


    def print(self):
        """
        Print information about the random process

        Parameters
        ----------
        none

        Returns
        -------
        none
        """
        labels = self.calibrator.getAllLabels()
        theModel = self.calibrator.model

        print("\n\n Random process with discrepancy and experimental error")
        print("---------------------------------------------------------")
        print("   Number of of experimental data: ", self.nExp)
        print("   Parameters")
        for i, label in enumerate(theModel.paramLabels):
            print("       {:8} = {:.5f}".format(label, theModel.param[i]));

        print("   Hyperparameters")
        for i, label in enumerate(self.calibrator.hyperLabels):
            print("       {:8} = {:.5f}".format(label, self.calibrator.hyper[i]));
        print("   Variance of experimental data: {0:.6f}".format(self.calibrator.expSTD**2))


# -----------------------------------------------------------------------------
#                        Type D problem: KOH Gaussian process
# -----------------------------------------------------------------------------
class KOHGaussianProcess(randomProcess):
    """
    Gaussian processes that have the structure of
    x ~ (symbolic equation or GP of metamodel) + (GP of discrepancy) + (experimental error)

    Reference: M.C. Kennedy and A. O'Hagan (2001): Bayesian calibration of computer models,
    J.R. Statist. Soc. B (2001), 63, Part 3 , pp. 425-464.
    """

    def __init__(self,
                 xExperimental, yExperimental,
                 xSynthetic, tSynthetic, ySynthetic, calibrator):
        """
        Constructor of KOH GP
            Gaussian process with the special structure of KOH
        It includes three terms:
           etahat(x, t) + delta(x) + epsilon(x)

        etahat: GP surrogate for the model. Depends on points and parameters
        delta: GP for the discrepancy error
        epsilon: the experimental error ~ N(0, sd_meas^2)

        Parameters
        ----------
        xExperimental: inputs x for experimental datapoints
        yExperimental: outputs for experimental datapoints (only scalars yet!)
        xSynthetic: inputs x for synthetic datapoints
        tSynthetic: parameter values for synthetic data datapoints
        ySynthetic: outputs for synthetic datapoints
        hyperparameters: parameters of the model + hyperparameters of GP

        Returns
        -------
        KOH Gauss process object
        """
        self.xExp = xExperimental
        self.yExp = yExperimental
        self.nExp = len(xExperimental)

        self.xSyn = xSynthetic
        self.tSyn = tSynthetic
        self.ySyn = ySynthetic
        self.nSyn = len(xSynthetic)

        self.calibrator = calibrator


    def covarianceMatrix_vect(self):
        """
        Vectorized code
        Evaluate the covariance matrix when we fix the value of the
        experimental data, synthetic data, parameters theta and hyperparameters

        Parameters
        ----------
        ---

        Returns
        -------
          Sigma: covariance matrix
        """
        N = self.nExp
        M = self.nSyn

        Sigma = np.empty((N+M, N+M))
        x  = self.xExp
        xt = self.xSyn
        tt = self.tSyn

        theModel = self.calibrator.model
        thetax = np.tile(theModel.param, (N,1))#np.full((N, theModel.getNParam()), [theModel.param])#theModel.param
        covx = self.calibrator.covx
        covt = self.calibrator.covt
        covd = self.calibrator.covd
        s2 = self.calibrator.getExperimentalSTD()**2



        # Block 1,1 shape (N,N)
        Covx_1 = covx(x, x)
        Covt_1 = covt(thetax, thetax)
        Sigma[:N, :N] = Covx_1 * Covt_1

        # Ensure diagonal of Sigma[:N, :N] has s2 added
        np.fill_diagonal(Sigma[:N, :N], np.diag(Sigma[:N, :N]) + s2)

        # Block 1,2 and 2,1 Shape (N, M) and (M,N)
        Covx_12 = covx(x, xt)
        Covt_12 = covt(thetax, tt)

        Sigma[:N, N:N + M] = Covx_12*Covt_12
        Sigma[N:N + M, :N] = Sigma[:N, N:N + M].T

        # Block 2,2 Shape (M, M)
        Covx_2 = covx(xt, xt)
        Covt_2 = covt(tt, tt)
        Sigma[N:N + M, N:N + M] = Covx_2 * Covt_2

        return Sigma


    def covarianceMatrix_vect_withdisc(self):
        """
        Evaluate the covariance matrix with discrepancy when we fix the value of the
        experimental data, synthetic data, parameters theta and hyperparameters

        Parameters
        ----------
        ---

        Returns
        -------
          Sigma: covariance matrix
        """
        N = self.nExp
        M = self.nSyn

        Sigma = np.empty((N+M, N+M))
        x  = self.xExp
        xt = self.xSyn
        tt = self.tSyn

        theModel = self.calibrator.model
        thetax = np.tile(theModel.param, (N,1))
        covx = self.calibrator.covx
        covt = self.calibrator.covt
        covd = self.calibrator.covd
        s2 = self.calibrator.getExperimentalSTD()**2

        # Block 1,1 shape (N, N)
        Covx_1 = covx(x, x)
        Covt_1 = covt(thetax, thetax)
        Covd_1 = covd(x, x)
        Sigma[:N, :N] = Covx_1 * Covt_1 + Covd_1

        # Ensure diagonal of Sigma[:N, :N] has s2 added
        np.fill_diagonal(Sigma[:N, :N], np.diag(Sigma[:N, :N]) + s2)

        # Block 1,2 and 2,1 Shape (N, M) and (M, N)
        Covx_12 = covx(x, xt)
        Covt_12 = covt(thetax, tt)
        Sigma[:N, N:N + M] = Covx_12*Covt_12
        Sigma[N:N + M, :N] = Sigma[:N, N:N + M].T

        # Block 2,2 Shape (M, M)
        Covx_2 = covx(xt, xt)
        Covt_2 = covt(tt, tt)
        Sigma[N:N + M, N:N + M] = Covx_2 * Covt_2

        return Sigma


    def eval_vect(self, Xstar):
        """
        Vectorized code
        Evaluate mean and std of the GP at points Xstar. The parameters theta
        and the hyperparameters have been set before.

        Parameters
        ----------
        Xstar: array of input points where we want to evaluate the GP
               The 2nd dimension should be equal to the dimension of the
               input variables x

        Returns
        -------
        ystar: mean at every point of Xstar
        np.sqrt(diag): Sqrt of the diagonal of the covariance matrix

        """
        N = self.nExp
        M = self.nSyn

        theModel = self.calibrator.model
        thetax = np.tile(theModel.param, (N,1))
        covx = self.calibrator.covx
        covt = self.calibrator.covt
        covd = self.calibrator.covd
        s2 = self.calibrator.getExperimentalSTD()**2

        x  = self.xExp
        xt = self.xSyn
        tt = self.tSyn

        xst = Xstar
        Nstar = len(Xstar)
        ystar = np.zeros((Nstar,1))
        thetast = np.tile(theModel.param, (Nstar, 1))

        # covariance matrix at (e)xisting data, not Xstar
        Kee = self.covarianceMatrix_vect()
        Kee = Kee + np.diag(np.repeat(1e-8, N + M))
        Ken = np.zeros((N+M, Nstar))

        #x-xstar block Shape (N, Nstar)
        Covx_en = covx(x, xst)
        Covt_en = covx(thetax, thetast)
        Ken[:N,:Nstar] = Covx_en*Covt_en

        #xtilde-xstar block, Shape (M, Nstar)
        Covxtxst_en = covx(xt, xst)
        Covttth_en = covt(tt, thetast)
        Ken[N:M+N,:Nstar] = Covxtxst_en*Covttth_en

        # xstar-xstar block, Shape (Nstar, Nstar)
        Knn = np.zeros((Nstar, Nstar))
        Covxstxst_nn = covx(xst, xst)
        Covthstthst_nn = covt(thetast, thetast)
        Knn[:Nstar, :Nstar] = Covxstxst_nn*Covthstthst_nn
        np.fill_diagonal(Knn[:Nstar, :Nstar], np.diag(Knn[:Nstar, :Nstar]) + s2)

        y = np.concatenate([self.yExp, self.ySyn])
        y = np.atleast_2d(y).T if self.calibrator.getOutputDimension() == 1 else np.atleast_2d(y)

        L = np.linalg.cholesky(Kee)
        v = np.linalg.solve(L, y)
        u = np.linalg.solve(L.T, v)
        ystar = np.matmul(Ken.T, u)

        v = np.linalg.solve(L, Ken)
        K2 = np.matmul(v.T,v)

        Sigma = Knn - K2
        diag = np.diag(Sigma).copy()

        tol = 1e-8
        diag[np.abs(diag) < tol] = 0.0

        return ystar, np.sqrt(abs(diag))


    def eval_vect_withdisc(self, Xstar):
        """
        Vectorized code
        Evaluate mean and std of the GP including discrepancy at points Xstar. The parameters theta
        and the hyperparameters have been set before.

        Parameters
        ----------
        Xstar: array of input points where we want to evaluate the GP
               The 2nd dimension should be equal to the dimension of the
               input variables x

        Returns
        -------
        ystar: mean at every point of Xstar
        np.sqrt(diag): Sqrt of the diagonal of the covariance matrix

        """
        N = self.nExp
        M = self.nSyn

        theModel = self.calibrator.model
        thetax = np.tile(theModel.param, (N,1))
        covx = self.calibrator.covx
        covt = self.calibrator.covt
        covd = self.calibrator.covd
        s2 = self.calibrator.getExperimentalSTD()**2

        x = self.xExp
        xt = self.xSyn
        tt = self.tSyn

        xst = Xstar
        Nstar = len(Xstar)
        ystar = np.zeros((Nstar,1))
        thetast = np.tile(theModel.param, (Nstar, 1))
        # covariance matrix at (e)xisting data, not Xstar
        Kee = self.covarianceMatrix_vect_withdisc()
        Kee = Kee + np.diag(np.repeat(1e-8, N + M))
        Ken = np.zeros((N + M, Nstar))


        # x-xstar block, Shape (N, Nstar)
        Covx_en = covx(x, xst)
        Covdx_en = covd(x, xst)
        Covt_en = covt(thetax, thetast)
        Ken[:N, :Nstar] = Covx_en * Covt_en #+ Covdx_en

        # xtilde-xstar block, Shape (M, Nstar)
        Covxtxst_en = covx(xt, xst)
        Covttthst_en = covt(tt, thetast)
        Covdxtxst_en = covd(xt, xst)
        Ken[N:M + N, :Nstar] = Covxtxst_en * Covttthst_en #+ Covdxtxst_en

        # xstar - xstar block, Shape (Nstar, Nstar)
        Covxstxst_nn = covx(xst, xst)
        Covthstthst_nn = covt(thetast, thetast)
        Covdxstxst_nn = covd(xst, xst)
        Knn = np.zeros([Nstar, Nstar])
        Knn[:Nstar, :Nstar] = Covxstxst_nn * Covthstthst_nn #+ Covdxstxst_nn
        np.fill_diagonal(Knn[:Nstar, :Nstar], np.diag(Knn[:Nstar, :Nstar]) + s2)

        y = np.concatenate([self.yExp, self.ySyn])
        y = np.atleast_2d(y).T if self.calibrator.getOutputDimension() == 1 else np.atleast_2d(
            y)

        L = np.linalg.cholesky(Kee)

        v = np.linalg.solve(L, y)
        u = np.linalg.solve(L.T, v)
        ystar = np.matmul(Ken.T, u)

        v = np.linalg.solve(L, Ken)
        K2 = np.matmul(v.T, v)

        Sigma = Knn - K2
        diag = np.diag(Sigma).copy()

        tol = 1e-8
        diag[np.abs(diag) < tol] = 0.0

        return ystar, np.sqrt(abs(diag))


    def print(self):
        """ Print information about the KOH GP.

        Parameters
        ----------
        none

        Returns
        -------
        none
        """
        theModel = self.calibrator.model

        print("\n\nKennedy & O'Hagan Gaussian process object")
        print("-----------------------------------------")
        print("   Number of of experimental data: ", self.nExp)
        print("   Number of synthetic data: ", self.nSyn)
        print("   Parameters")
        for i, label in enumerate(theModel.paramLabels):
            print("       {:8} = {:.5f}".format(label, theModel.param[i]));
        print("   Hyperparameters")
        for i, label in enumerate(theModel.hyperLabels):
            print("       {:8} = {:.5f}".format(label, theModel.hyper[i]));
        print("   Variance of experimental data: {0:.6f}".format(theModel.expSTD**2))


    @staticmethod
    def test(self):
        """Use this function to test the KOH model.

            Parameters
            ----------

            Returns
            -------
            Plot for testing KOH class, plotting prediction vs. experimental values
        """
        N = 5  # number of experimental datapoints
        M = 1  # number of synthetic datapoints

        #add
        theModel = self.calibrator.model

        # experimental data, including noise
        sd_meas = 0.02

        xExperimental = lhs(1,N)
        xExperimental = np.sort(norm.ppf(xExperimental), axis=0)
        zExperimental = trueModel(xExperimental)

        xSynthetic = lhs(1, M)
        xSynthetic = np.sort(norm.ppf(xSynthetic), axis=0)
        tSynthetic = lhs(1, M)
        tSynthetic = norm.ppf(tSynthetic, loc=1, scale=0.2)
        zSynthetic = theModel(xSynthetic, tSynthetic)

        MAP = np.array([1.75080631,2.11921379, 2.13769496, 0.07054854, 0.38814496, 0.82404103])
        MAP = np.array([1.43506401e+00, 9.87431762e-02, 1.08415737e+00,
                        2.28409672e-04, 1.05445038e+00, 3.45623837e+00])
        #MAP = np.array([1.1036364, 0.90275889, 0.90877033, 0.81975129, 0.91286113, 0.62265796])
        gpr = KOHGaussianProcess(xExperimental, zExperimental,
                                 xSynthetic, tSynthetic, zSynthetic,
                                 MAP[0], MAP[1], MAP[2], MAP[3], MAP[4], MAP[5],
                                 sd_meas)
        minTest = -1.5
        maxTest = 2.0
        nTest = 30

        xtest = np.empty((nTest, 1))
        xtest[:,0] = np.linspace(minTest, maxTest, nTest)

        ztest, zvariance = gpr.eval_vect_withdisc(xtest)

        plt.title('Test of KOH Gaussian process')
        plt.plot(xExperimental, zExperimental, 'o')
        plt.plot(xtest, ztest, '+-', label='GPR prediction')
        plt.show()
