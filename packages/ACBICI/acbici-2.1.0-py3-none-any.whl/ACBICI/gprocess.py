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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 16:09:02 2023

@author: Ignacio Romero, Christina Schenk
"""

#Python Packages:
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




# -----------------------------------------------------------------------------
#                      Gaussian process
# -----------------------------------------------------------------------------

class GaussianProcess():
    """
    A Gaussian process.
    """


    def __init__(self, X, z, mu, cov, noisesigma=0.0):
        """function for constructor of GP based processes

            Parameters
            ----------
            X: array of points where the data is known (N x dim)
            z: known values of the function evaluation at Z (N)
            mu: lambda function for the mean mu = mu(x)
            cov: lambda function for the covariance cov = cov(x,s')
            noisesigma: std of gaussian noise

            Returns
            -------
            Constructor with input variables/parameters
        """
        self.X = X
        self.z = z
        self.mu = mu
        self.cov = cov
        self.N = len(X)
        self.snoise = noisesigma


    def covarianceMatrix(self):
        """function for covarianceMatrix

            Parameters
            ----------
            self: constructor

            Returns
            -------
            Sigma: covariance matrix
        """
        N = self.N
        Sigma = np.zeros((N,N))
        for i in range(N):
            x = np.array([self.X[i,:]])
            for j in range(i+1):
                y = np.array([self.X[j,:]])

                tmp = self.cov(x, y)
                Sigma[i, j] = tmp.item()
                Sigma[j, i] = tmp.item()

            Sigma[i, i] += self.snoise * self.snoise

        return Sigma



    def info(self):
        """info function

            Parameters
            ----------
            self: constructor

            Returns
            -------
            print number of data points
        """
        print("Gaussian process object")
        print("N datapoints ", self.N)



    def eval(self, Xstar):
        """eval function to return mean and std of the GP at points Xstar, when
        the parameters theta and the hyperparameters have been set before.

        Parameters
        ----------
        self: constructor
        Xstar: array of input points of dimension number of points where we want to evaluate it x 1

        Returns
        -------
        zstar: mean
        np.sqrt(diag): standard deviation
        """
        N = self.N
        Nstar = Xstar.shape[0]

        # e: existing, n: new
        mue = np.zeros(N)
        for i in range(N):
            #.item() to explicitly extract single element from array to avoid depreciation warnings
            mue[i] = self.mu(self.X[i,:].item())

        mun = np.zeros(Nstar)
        for i in range(Nstar):
            mun[i] = self.mu(Xstar[i,:].item())

        Kee = self.covarianceMatrix()

        # mean and variance vectors at Xstar
        zstar = np.zeros(Nstar)

        Ken = np.zeros([N, Nstar])
        for i in range(N):
            x = np.array([self.X[i, :]])

            for j in range(Nstar):
                y = np.array([Xstar[j, :]])
                Ken[i, j] = self.cov(x, y).item()

        Knn = np.zeros([Nstar, Nstar])
        for i in range(Nstar):
            x = np.array([Xstar[i, :]])

            for j in range(i+1):
                y = np.array([Xstar[j, :]])

                tmp = self.cov(x, y)

                Knn[i, j] = tmp.item()
                Knn[j, i] = tmp.item()

            Knn[i, i] += self.snoise * self.snoise

        shift = np.zeros(N)
        for i in range(N):
            shift[i] = self.z[i] - mue[i]

        L = np.linalg.cholesky(Kee)
        u = np.linalg.solve(L, shift)
        u = np.linalg.solve(np.transpose(L), u)
        zstar = np.matmul(Ken.T, u) + mun

        K2 = np.linalg.solve(L, Ken)
        K2 = np.matmul(np.transpose(K2), K2)
        Sigma = Knn - K2
        diag = np.diagonal(Sigma).copy()

        tol = 1e-8
        diag[np.abs(diag) < tol] = 0.0

        if np.min(diag) < 0.0:
            print("\n Singular diagonal:")
            #print(diag)
            sys.exit("Abort: Negative diagonal found")

        return zstar, np.sqrt(diag)



    @staticmethod
    def test():
        """Use this function to test the vanilla Gaussian process. A random
            vector of datapoints is created, and a GP is built from them, using
            random hyperparameters. Finally, plots are generated to see that everything
            works ok.

            Parameters
            ----------
            Returns
            -------
            Plot for validating plain GP with noise
        """

        N = np.random.randint(8, 12)
        xExperimental = (10.0*np.sort(lhs(1, N), axis=0))-5.0
        zExperimental = np.concatenate(trueModel(xExperimental))

        beta = np.array([[np.random.rand()+1.0]])
        lamb = np.array([[np.random.rand()+0.5]])
        noise = np.random.rand()*0.1

        # functional form of the covariance and mean. The latter might be 0
        cov = lambda x, y: np.exp(-np.sum(beta*(np.abs(x-y)**2)))/lamb + noise*noise
        mu  = lambda x: np.sin(x)
        snoise = 0.1

        gpr = GaussianProcess(xExperimental, zExperimental, mu, cov, snoise)
        gpr.info()

        minTest = np.min(xExperimental)
        maxTest = np.max(xExperimental)
        nTest = np.random.randint(30, 70)
        xtest = np.empty((nTest, 1))
        xtest[:, 0] = np.linspace(minTest, maxTest, nTest)

        ztest, zstd = gpr.eval(xtest)

        plt.style.use('tableau-colorblind10')
        plt.figure()
        plt.title("Validation of plain Gaussian process with noise")
        plt.plot(xExperimental, zExperimental, 'o', label='known data')
        plt.plot(xtest, ztest, '+-', label='GPR prediction')
        plt.fill_between(np.concatenate(xtest),
                         ztest-zstd, ztest+zstd, alpha=.2)

        plt.legend(loc='best')
        plt.show()
