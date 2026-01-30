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
from abc import ABC, abstractmethod
import corner
from datetime import datetime
import emcee
import math
import matplotlib.pyplot as plt
import numpy as np
from numpy import linalg as LA
import os
import math
from pyDOE import lhs
import random
import seaborn as sns
import socket
from scipy import stats as st
from scipy.stats import multivariate_normal, norm
from statistics import median, mode
from scipy.signal import find_peaks
import sys
import uuid

from .randomprocess import KOHGaussianProcess, expensiveGaussianProcess, inexpKOHGaussianProcess
from .kernels import *
from .priors import *
from .vbmc import *

import inspect
import ast
import textwrap

def is_function_effectively_empty(func):
    try:
        source = inspect.getsource(func)
        source = textwrap.dedent(source)  # Remove leading indentation!
        tree = ast.parse(source)
    except Exception:
        return False

    # Find the function definition node
    func_def = next((node for node in tree.body if isinstance(node, ast.FunctionDef)), None)
    if func_def is None:
        return False

    body = func_def.body

    # Skip a docstring if present
    if body and isinstance(body[0], ast.Expr) and \
       isinstance(body[0].value, (ast.Str, ast.Constant)) and \
       isinstance(getattr(body[0].value, 'value', None), str):
        body = body[1:]

    # True if empty or only 'pass' statements
    return (not body) or all(isinstance(stmt, ast.Pass) for stmt in body)

# Try to import scikit-sparse, set a flag if it's unavailable
try:
    from sksparse.cholmod import cholesky as cholsp
    sksparse_available = True
    import scipy.sparse as sp
except ImportError:
    sksparse_available = False
    print("scikit-sparse not available. Falling back to dense Cholesky decomposition.")


def average_pairwise_distance(data):
    """
    Given an two dimensional array of size n x m, this function assume that
    it corresponds to n vectors of data, each of them of length m. Then,
    it finds the average Euclidean distance among all data

    Parameters
    ----------
    data: a numpy array of dim n x m, containing n vectors of size m.

    Returns
    -------
    The average mean Euclidean distance between all pairs of data.
    """
    n = data.shape[0]
    diff = data[:, np.newaxis, :] - data  # Shape: (n, n, features)
    distances = np.linalg.norm(diff, axis=-1)
    upper_triangle = distances[np.triu_indices(n, k=1)]  # Exclude diagonal
    return upper_triangle.mean()


def printStatistics(names, samples, file=sys.stdout):
    """
    Prints a nice description of the main statistics of the sample.

    Parameters
    ----------
    names: an array of strings with the names of the variables in samples
    samples: an array of samples. Each row has the same length as 'names'

    Returns
    -------
    None
    """
    res = st.describe(samples, axis=0)
    MAP = findApproximateMAP(samples)
    print("\n-------------------------------------------------------------------------", file=file)
    print("                 Summary statistics ({:d} samples)".format(
        np.shape(samples)[0]), file=file)
    print("\n Parameter     Mean     Median     app-MAP    Variance       95%-credible",
          file=file)
    print("---------------------------------------------------------------------------",
          file=file)
    for k, nn in enumerate(names):
        # Compute quantiles of the posterior distribution using the normal
        # distribution. Warning: this is only true if the distribution is
        # normal. Otherwise, it is an approximation
        credible_intervals = np.percentile(samples[:, k], [2.5, 50.0, 97.5], axis=0)
        low = credible_intervals[0]
        med = credible_intervals[1]
        upp = credible_intervals[2]
        print(" {:10} {:.3e}  {:.3e}  {:.3e}  {:.3e}  [{:.3e}, {:.3e}]".format(
            nn, res.mean[k], med, MAP[k], res.variance[k], low, upp), file=file)


def findApproximateMAP(data):
    """
    Obtains the approximate value of the MAP estimate in each column of x.

    Parameters
    ----------
    data: an array of samples. Each row is a vector or samples of the
    various variables. Each column corresponds to many samples of the
    same variable.

    Returns
    -------
    MAP: the map of each column
    """
    nrows = data.shape[0]
    nvars = data.shape[1]
    nbins = 2*math.ceil(math.log2(nrows))
    MAP = np.zeros((nvars,))

    for k, column in enumerate(data.T):
        hist, bins = np.histogram(column, bins=nbins)#, density=True)
        max_bin = np.argmax(hist)
        bin_range = bins[max_bin:max_bin+2]
        bin_center = (bin_range[0] + bin_range[1]) / 2
        MAP[k] = bin_center

    return MAP


def log_multivariate_normal_pdf_sparse(x, mu, cov):
    """
    Calculates the log likelihood with sparse Cholesky decomposition

    Parameters
    ----------
    x: the value where the log-likelihood is to be evaluated
    mu: the mean vector. dim(mu) = dim(x)
    cov: the covariance matrix. dim(cov) = dim(x) x dim(x)

    Returns
    -------
    log-likelihood or the log-likelihood minus a constant that does
    not depend on x.
    """
    factor = cholsp(cov)  # scikit-sparse Cholesky decomposition
    L = factor.L()  # Obtain the lower triangular matrix

    # Calculate the log PDF
    x_mu = x - mu

    # Solve for y in L y = x - mu
    y = factor.solve_A(x_mu)  # This solves L * y = x_mu efficiently

    # Log determinant using Cholesky
    log_det_cov = 2 * np.sum(np.log(L.diagonal()))
    log_pdf = -0.5 * (log_det_cov + np.dot(y, y))

    return log_pdf


def log_multivariate_normal_pdf(x, mu, cov):
    """
    Calculates the log likelihood with dense Cholesky decomposition

    Parameters
    ----------
    x: the value where the log-likelihood is to be evaluated
    mu: the mean vector. dim(mu) = dim(x)
    cov: the covariance matrix. dim(cov) = dim(x) x dim(x)

    Returns
    -------
    log-likelihood or the log-likelihood minus a constant that does
    not depend on x.
    """
    # Obtain the lower triangular matrix
    L = np.linalg.cholesky(cov)

    # Calculate the log PDF
    x_mu = x - mu

    # Solve for y in L y = x - mu
    y = np.linalg.solve(L, x_mu)  # This solves L*y = x_mu

    # Log determinant using Cholesky
    log_det_cov = 2 * np.sum(np.log(np.diagonal(L)))
    log_pdf = -0.5 * (log_det_cov + np.dot(y, y))

    return log_pdf


# -----------------------------------------------------------------------------
#             Abstract class of the model that will be calibrated
# -----------------------------------------------------------------------------

class ACBICImodel(ABC):

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)

        instance.xdim = 0
        instance.ydim = 1
        instance.param = []
        instance.paramLabels = []
        instance.priors = []
        return instance


    @abstractmethod
    def __init__(self):
        pass


    def addParameter(self, *, label=None, prior):
        """
        Appends a parameter to the model that will be calibrated.

        Parameters
        ----------
        label: a string with the name of the parameter.
        prior: a prior distribution for the parameter

        Example:
        self.addParameter(label=r'$\theta$', prior=Uniform(a=1.0, b=2.0))

        Returns
        -------
        None
        """
        nparam = len(self.param)
        self.param = np.zeros(nparam+1)

        if label is None:
            label = "par" + str(len(self.paramLabels))
        self.paramLabels.append(label)
        self.priors.append(prior)


    def getInputDimension(self):
        """
        Returns the dimension of the input variables of
        the model.

        Parameters
        ----------
        None

        Returns
        -------
        The dimension of the input variables
        """
        return self.xdim


    def getOutputDimension(self):
        """
        Returns the dimension of the output variables of the model = number of tasks.

        Parameters
        ----------
        None

        Returns
        -------
        The dimension of the output variables
        """
        return self.ydim


    def getNParam(self):
        """
        Returns the number of parameters in the model.

        Parameters
        ----------
        None

        Returns
        -------
        The number of parameters.
        """
        return len(self.param)


    @abstractmethod
    def symbolicModel(self, x, t):
        """
        Evaluates the model f(x,t), the expression that we want to calibrate.

        Parameters
        ----------
        x: an np array. On each row, a vector of observable inputs
        t: an np array. On each row, a vector of parameters

        Returns
        -------
        An np array, value f(x,t) at each of the pairs (x_i, t_i)
        """
        pass


# -----------------------------------------------------------------------------
#                          Abstract calibration types
# -----------------------------------------------------------------------------
class Calibrator(ABC):

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.name = None
        instance.model = None
        instance.kernel = None

        instance.xExp = None
        instance.yExp = None
        instance.nExp = 0
        instance.xSyn = None
        instance.tSyn = None
        instance.ySyn = None
        instance.nSyn = 0
        instance.Sigma = None

        instance.hyper = []
        instance.hyperLabels = []
        instance.hyperPriors = []

        instance.knownEE = False
        instance.expSTD = -1.0
        instance.expPrior = None

        instance.odirectory = None
        instance.logfilename = None

        instance.usesSymbolicModel = True
        # instance.usesOriginalSymbolicModel = True

        return instance


    @abstractmethod
    def __init__(self, aModel):
        """
        Constructor

        Parameters
        ----------
        aModel: an ACBICI Model

        Returns
        -------
        None
        """
        pass


    def addHyperparameter(self, name, prior):
        """
        Appends a hyperparameter to the calibration object.

        Parameters
        ----------
        name: (string) the name of the hyperparameter
        prior: a prior probability

        Returns
        -------
        None
        """

        nhyper = len(self.hyper)
        self.hyper = np.zeros(nhyper+1)
        self.hyperLabels.append(name)
        self.hyperPriors.append(prior)


    @abstractmethod
    def calibrate(self, *, method="mcmc", nsteps=10000, burn=0.2, thin=1, nwalkers=16, nsynthetic=30):
        """
        This is the main function of the calibrator. It taks care of the whole
        calibration process.

        Parameters
        ----------
        nsteps (optional): the number of MCMC steps
        burn: (optional): the ration of burn in samples
        thin: 1 if thinning is to be performed.
        nwalkers: number of walkers for parallel MCMC
        nsynthetic: Number of synthetic points to be generated if a
                   surrogate is built. If the calibrator does not u
                   use a surrogate, the option is ignored.

        Returns
        -------
        None
        """
        pass


    def gaussianLogLikelihood(self, x, mu, sigma, sparse=False):
        """
        Calculate the log-likelihood of a Gaussian variable at a value, given its
        mean and covariance.

        Parameters
        ----------
        x: the value where the log-likelihood is to be evaluated
        mu: the mean vector. dim(mu) = dim(x)
        sigma: the covariance matrix. dim(sigma) = dim(x) x dim(x)
        sparse: flag for using sparse Cholesky, requires scikit-sparse package,
        default=False uses dense Cholesky

        Returns
        -------
        log-likelihood or the log-likelihood minus a constant that does
        not depend on x.
        """
        if sksparse_available and sparse:
            try:
                sigma = sp.csc_matrix(sigma)

                # Set threshold for chop off
                trace = sigma.diagonal().sum()
                num_diagonal_elements = sigma.shape[0]
                norm = trace/num_diagonal_elements

                # Create a mask for non-diagonal entries
                rows, cols = sigma.nonzero()  # Get row, col indices of non-zero entries
                non_diagonal_mask = (rows != cols)  # Identify non-diagonal entries

                # Get the values of the non-diagonal entries
                non_diagonal_values = sigma.data[non_diagonal_mask]

                threshold = 1e-5*norm
                # Create a mask for values below the threshold
                below_threshold_mask = np.abs(non_diagonal_values) < threshold

                # Set the non-diagonal values below the threshold to zero
                #sigma.data[non_diagonal_mask][below_threshold_mask] = 0

                # Remove zero entries from the sparse structure
                sigma.eliminate_zeros()

                ll = log_multivariate_normal_pdf_sparse(x, mu.flatten(), sigma)

            except np.linalg.LinAlgError:
                tol = 1e-6
                print("The matrix is not positive definite. Adding small diagonal proportional to trace *", tol)
                np.fill_diagonal(sigma, sigma.diagonal() + tol * sigma.trace())
                sigma = sp.csc_matrix(sigma)
                # Set threshold for chop off
                trace = sigma.diagonal().sum()
                num_diagonal_elements = sigma.shape[0]
                norm = trace / num_diagonal_elements
                threshold = 1e-5*norm

                # Create a mask for non-diagonal entries
                rows, cols = sigma.nonzero()  # Get row, column indices of non-zero entries
                non_diagonal_mask = (rows != cols)  # Identify non-diagonal entries

                # Get the values of the non-diagonal entries
                non_diagonal_values = sigma.data[non_diagonal_mask]

                # Create a mask for values below the threshold
                below_threshold_mask = np.abs(non_diagonal_values) < threshold

                # Set the non-diagonal values below the threshold to zero
                sigma.data[non_diagonal_mask][below_threshold_mask] = 0
                sigma.eliminate_zeros()  # Remove zero entries from the sparse structure

                ll = log_multivariate_normal_pdf_sparse(x, mu.flatten(), sigma)
        else:
            try:
                ll = log_multivariate_normal_pdf(x, mu.flatten(), sigma)

            except np.linalg.LinAlgError:
                tol = 1e-6
                print("Matrix is not positive definite. Adding small diagonal proportional to trace *", tol)

                np.fill_diagonal(sigma, sigma.diagonal() + tol*sigma.trace())
                ll = log_multivariate_normal_pdf(x, mu.flatten(), sigma)
        return ll


    def genericCalibration(self, *, method="mcmc", nsteps=10000, burn=0.2, thin=1, nwalkers=16,
                  fposterior="samples", flogprob="logprob", flogprior="logprior"):
        """
        This function takes care of the calibration process, once all the parameters
        and required functions have been taken care of. It should not be called
        directly by the user but from a derived calibrator.

        Parameters
        ----------
        method: "mcmc": Markov Chain Monte Carlo (default)
                 "vbmc":  Variational Bayesian Monte Carlo using pyvbmc
                 "vbmcsimple": a simplified Variational Bayes Monte Carlo solver
        nsteps: number of MCMC steps
        burn: ratio of burn in samples in MCMC
        thin: 1 if thinning is to be performed in MCMC
        nwalkers: number of walkers for parallel MCMC
        fposterior: filename where the posteriors will be written
        flogprob: filename where the log-pdf will be written
        flogprior: filename where the priors will be written

        Returns
        -------
        None
        """

        if method == "vbmcsimple":
            vbmc = DiagonalVBmc(self)
            mu, sigma = vbmc.fit()
            posterior = vbmc.sample_posterior(1000)
            np.save(self.odirectory+'/'+fposterior+'.npy', posterior)

        elif method == "vbmc":
            vbmc = VBmc(self)
            vbmc.fit()
            posterior = vbmc.sample_posterior(2000)
            np.save(self.odirectory+'/'+fposterior+'.npy', posterior)

        else:
            self.mcmcCalibration(nsteps=nsteps, burn=burn, thin=thin, nwalkers=nwalkers,
                  fposterior=fposterior, flogprob=flogprob, flogprior=flogprior)

        return


    def mcmcCalibration(self, *, nsteps=10000, burn=0.2, thin=1, nwalkers=16,
                        fposterior="samples", flogprob="logprob", flogprior="logprior"):
        """
        Markov chain Monte Carlo calibration.

        Parameters
        ----------
        nsteps: number of MCMC steps
        burn: ratio of burn in samples in MCMC
        thin: 1 if thinning is to be performed in MCMC
        nwalkers: number of walkers for parallel MCMC
        fposterior: filename where the posteriors will be written
        flogprob: filename where the log-pdf will be written
        flogprior: filename where the priors will be written

        Returns
        -------
        None
        """

        nph = self.getNPHE()
        sampler = emcee.EnsembleSampler(nwalkers, nph, self.logPosterior, args=[])

        p0 = np.empty([nwalkers, nph])
        for i in range(nwalkers):
            p0[i,:] = self.randomize().reshape((nph,))

        sampler.run_mcmc(p0, nsteps, thin_by=thin, progress=True,
                         skip_initial_state_check=False)

        nBurn = math.ceil(nsteps*burn)
        posterior = sampler.get_chain(flat=True, thin=thin, discard=nBurn)
        logprob = sampler.get_log_prob(flat=True, thin=thin, discard=nBurn)
        logprior = sampler.get_blobs(flat=True, thin=thin, discard=nBurn)

        # save sample results and log probabilities to files:
        np.save(self.odirectory+'/'+fposterior+'.npy', posterior)
        np.save(self.odirectory+'/'+flogprob+'.npy', logprob)
        np.save(self.odirectory+'/'+flogprior+'.npy', logprior)

        # if you get an autocorrelation time error of this type:
        # emcee.autocorr.AutocorrError: The chain is shorter than 50 times
        # the integrated autocorrelation time for 1 parameter(s). Use this
        # estimate with caution and run a longer chain!
        # N / 50 = 22; tau: [22.14675566 23.67994754]
        # then run again for minimum n_mcmc steps where
        # n_mcmc=max(tau)*len(p)*(1+burnFraction)*nwalkers, e.g.
        # 24*2*1.2*32 = 1843 with rounded to full digits, 1843 being nMCMCsteps
        # and repeat until you ran it for enough MCMC samples.
        self.printlog("\n\n Process report:")
        self.printlog("   - Chain length:", len(posterior))
        self.printlog("   - Burn in:", nBurn)
        self.printlog("   - N walkers:", nwalkers)
        self.printlog("   - Mean acceptance fraction: {0:.3f}".format(
            np.mean(sampler.acceptance_fraction)))

        # Print autocorrelation error and Proceed with the next steps.
        try:
            autocorr_time = sampler.get_autocorr_time(thin=thin, discard=nBurn)
            self.printlog("   - Mean autocorrelation time: {0:.3f} steps".format(
                np.mean(autocorr_time)))

            # ESS calculation
            N_post = len(posterior)  # already flat, thin, and burn-discarded

            ess_per_param = N_post / autocorr_time
            ess_per_param_2tau = N_post / (2.0 * autocorr_time)  # optional alternative

            self.printlog("   - N post-burn/thinned samples (flat): {}".format(N_post))
            self.printlog("   - ESS per parameter (N/tau): " +
                          ", ".join([f"{e:.1f}" for e in ess_per_param]))
            # emcee's convention closer to N/tau
            self.printlog("   - Mean ESS (N/tau): {0:.1f}".format(np.mean(ess_per_param)))

            # optional conservative variant
            self.printlog("   - Mean ESS (N/(2*tau), conservative): {0:.1f}".format(
                np.mean(ess_per_param_2tau)))
            labels = self.getAllLabels()
            chain = sampler.get_chain(discard=nBurn, thin=thin)


            # Plot autocorrelation for all parameters
            # compute Rhat (Gelman-Rubin statistic)
            # here split Rhat, this means: split each walker's chain into two halves, doubling the number of chains and catching non-stationarity
            # compare between-walker variance and within-walker variance
            # Rhat around 1: walkers agree -> good mixing/convergence
            def split_rhat(ch):
                """
                Split-Rhat per parameter.
                ch: array (nsteps, nwalkers, nph)
                returns: rhat array (nph,)
                """
                nsteps, nwalkers, npar = ch.shape
                if nsteps < 4:
                    return np.full(npar, np.nan)

                # split each walker into two halves along time axis
                half = nsteps // 2
                ch1 = ch[:half, :, :]
                ch2 = ch[half:2*half, :, :]
                split = np.concatenate([ch1, ch2], axis=1)   # (half, 2*nwalkers, npar)

                #m = split.shape[1]  # number of chains
                n = split.shape[0]  # length per chain

                # chain means and variances (per chain, per param)
                chain_means = np.mean(split, axis=0)         # (m, npar)
                chain_vars  = np.var(split, axis=0, ddof=1)  # (m, npar)

                # within-chain variance W
                W = np.mean(chain_vars, axis=0)             # (npar,)

                # between-chain variance B
                B = n * np.var(chain_means, axis=0, ddof=1)

                # marginal posterior variance estimate
                var_hat = (n - 1) / n * W + B / n

                Rhat = np.sqrt(var_hat / W)
                return Rhat


            rhat = split_rhat(chain)
            # Plot Rhat per parameter
            labels = self.getAllLabels()

            plt.figure(figsize=(8, 4))
            x = np.arange(nph)
            plt.bar(x, rhat)
            plt.axhline(1.01, linestyle='--')
            plt.axhline(1.05, linestyle=':')
            plt.xticks(x, labels, rotation=45, ha='right')
            plt.ylabel("split-Rhat")
            plt.tight_layout()
            plt.savefig(self.odirectory + "/rhat_per_param.png")
            plt.close()
            self.printlog("   - Rhat per parameter (split): " +
                          ", ".join([f"{r:.3f}" for r in rhat]))
            self.printlog("   - Max Rhat: {0:.3f}".format(np.nanmax(rhat)))


            # Computing autocorrelation using FFT and inverse FFT with zero-padding to length 2n.
            # FFT is intinsically, meaning it assumes the input signal is periodic and wraps around at the edges.
            # So, zero-padding to length 2n to prevent circular convolution effects.
            def autocorr_func(x):
                n = len(x)
                x = x - np.mean(x)
                f = np.fft.fft(x, n=2 * n)
                acf = np.fft.ifft(f * np.conjugate(f))[:n].real
                acf /= acf[0]
                return acf


            for param_idx in range(nph):
                samples = chain[:, :, param_idx].reshape(-1)
                acf = autocorr_func(samples)

                plt.figure()
                plt.plot(acf, linestyle='-', marker='')
                plt.xlabel('Lag')
                plt.ylabel('Autocorrelation for '+ labels[param_idx])
                plt.savefig(self.odirectory + '/autocorrelation_param'+str(param_idx)+'.png')
                plt.close()

        except emcee.autocorr.AutocorrError as e:
            msg = "   - Autocorrelation error occurred: {}".format(str(e))
            warn = "   - WARNING: Chain may be too short, results may not have converged."

            # print messages to console
            print(msg)
            print(warn)

            # log messages to the log file
            self.printlog(msg)
            self.printlog(warn)


    def getAllLabels(self):
        """
        Retrieves the labels (strings) of all the variables that need to be calibrated:
        the model parameters, the calibrator hyperparameters (if any) and the
        experimental error (if unknown).

        Parameters
        ----------
        --

        Return
        ------
        Array of labels.
        """
        labels = self.model.paramLabels + self.hyperLabels

        if not self.knownEE:
            labels.append(r'$\sigma$')
        return labels


    def getExperimentalSTD(self):
        """
        Parameters
        ----------
          --

        Return
        ------
        The value of the experimental error.
        """
        return self.expSTD


    def generateSyntheticData(self, *, npoints=30):
        """
        Generate synthetic (random) input/parameters pairs,
        run the model and store the synthetic (x, theta, y) triplets
        that will be used to feed the surrogate.

        Parameters
        ----------
          npoints: number of synthetic points to be generated.

        Return
        ------
          None
        """
        M = npoints
        theModel = self.model
        xDim = theModel.getInputDimension()
        pDim = theModel.getNParam()

        xmin = np.min(self.xExp, axis=0)
        xmax = np.max(self.xExp, axis=0)

        xSynthetic = lhs(xDim, M)*(xmax-xmin)+xmin

        pmin = np.zeros(pDim)
        pmax = np.zeros(pDim)
        for i, pr in enumerate(theModel.priors):
            pmin[i] = pr.ppf(0.02)
            pmax[i] = pr.ppf(0.98)

        pSynthetic = lhs(pDim, M)*(pmax-pmin)+pmin
        ySynthetic = self.model.symbolicModel(xSynthetic, pSynthetic).reshape(-1, 1)

        xy = np.hstack((xSynthetic, pSynthetic, ySynthetic))
        np.savetxt(self.odirectory+"/synthetic.dat", xy)


    def getNParam(self):
        """
        Returns the number of parameters in the model that is being
        calibrated.

        Parameters
        ----------
        --

        Return
        ------
        The number of parameters.
        """
        return self.model.getNParam()


    def getNPHE(self):
        """
        Returns the number of variables that need to be
        calibrated in the problem. This includes the parameters in the model,
        the hyperparameters in the GP (if any) and the experimental error (if
        unknown).

        Parameters
        ----------
        --

        Return
        ------
        The number of parameters + hyperparameters (if any) + experimental
        error (if any) in the calibration.
        """
        nexp = 0
        if not self.knownEE:
            nexp = 1
        return self.getNParam() + self.getNHyper() + nexp


    def getNHyper(self):
        """
        Returns the number of hyperparameters in the GP (if any).

        Parameters
        ----------
        --

        Return
        ------
        The number hyperparameters in the calibration (>=0)
        """
        return len(self.hyper)


    @abstractmethod
    def logLikelihood_vect(self):
        """
        Vectorized function that calculates the log-likelihood

        Parameters
        ----------
        None

        Return
        ------
        None
        """
        pass


    def logPriors(self):
        """
        Logarithm of priors samples for the PHE.

        Parameters
        ----------
        None

        Returns
        -------
        Array of log-priors of params + hyperparams + exp
        """
        logp = np.zeros(self.getNPHE())

        nparam = self.getNParam()
        for k, pr in enumerate(self.model.priors):
            logp[k] = pr.logProbability(self.model.param[k])

        nhyper = self.getNHyper()
        for k, pr in enumerate(self.hyperPriors):
            logp[nparam+k] = pr.logProbability(self.hyper[k])

        if not self.knownEE:
            pr= self.expPrior
            logp[nparam+nhyper] = pr.logProbability(self.expSTD)

        return logp


    def logPosterior(self, PHE):
        """
        Log posterior computation

        Parameters
        ----------
        PHE: an np array with the parameters, hyperparameters (if any), expError (if any)

        Returns
        -------
        logPosterior / -inf if the Hyperpar-Par-Exp have invalid values
        """
        self.storePHE(PHE)

        logPrior = np.sum(self.logPriors())
        if math.isinf(logPrior):
            return -np.inf

        logLike = self.logLikelihood_vect()
        return logLike + logPrior


    def PHEbounds(self):
        """
        Compute lower and upper bounds for the parameters to be calibrated

        Parameters
        ----------
        None

        Returns
        -------
        lower: array with lower bounds. Can be -np.inf
        upper: array with upper boudns. Can be +np.in
        """
        nphe = self.getNPHE()
        upper = np.zeros(nphe)
        lower = np.zeros(nphe)

        nparam = self.getNParam()
        for k, pr in enumerate(self.model.priors):
            lower[k], upper[k] = pr.bounds()

        for k, pr in enumerate(self.hyperPriors):
            lower[nparam+k], upper[nparam+k] = pr.bounds()

        if not self.knownEE:
            nhyper = len(self.hyper)
            lower[nparam+nhyper], upper[nparam+nhyper] = self.expPrior.bounds()

        return lower, upper


    def PHEguess(self):
        """
        Compute lower and upper bounds guesses for the parameters to be calibrated

        Parameters
        ----------
        None

        Returns
        -------
        lower: array with lower guess. Can be -np.inf
        upper: array with upper guess. Can be +np.in
        """
        nphe = self.getNPHE()
        upper = np.zeros(nphe)
        lower = np.zeros(nphe)

        nparam = self.getNParam()
        for k, pr in enumerate(self.model.priors):
            lower[k], upper[k] = pr.guessInterval()

        for k, pr in enumerate(self.hyperPriors):
            lower[nparam+k], upper[nparam+k] = pr.guessInterval()

        if not self.knownEE:
            nhyper = len(self.hyper)
            lower[nparam+nhyper], upper[nparam+nhyper] = self.expPrior.guessInterval()
            lower[nparam+nhyper] = 0.1
            upper[nparam+nhyper] = 1.0

        return lower, upper


    @abstractmethod
    def plot(self, *, compare=True, discrepancy=True, prior=True,
             trace=True, corner=True, pearson=True, prerror=True,
             onscreen=False, dumpfiles=True):
        """
        Abstract function for the plot generation.

        Parameters
        ----------
        Compare: generate data vs. predictions plot if True
        Discrepancy: generate a plot wit the discrepancy function if True
        prior: generate figure with prior probabilities for parameters if True
        trace: generate MCMC trace plots if True
        corner: generate corner plots for posterior if True
        pearson: generate correlation plot
        prerror: generate prediction error plot
        dumpfiles: write files to disk if True

        Returns
        -------
        None
        """
        pass


    def plotPredictionErrors(self, *, onscreen=True, dumpfiles=True):
        """
        Generate a figure illustrating the errors made by the calibrated model.

        Parameters
        ----------
        onscreen: if True, plot the figure on the screen
        dumpfiles: if True, write the figure on a file

        Returns
        -------
        None
        """
        errors = self.predictionError()
        if errors is None:
            return

        nout = self.model.getOutputDimension()

        fig, axes = plt.subplots(nout, 1, figsize=(8, 2*nout))
        axes = np.atleast_1d(axes)
        for i in range(nout):
            xmin = min(errors[:,i])
            xmax = max(errors[:,i])
            sns.histplot(errors[:,i], bins=10, kde=True, ax=axes[i],
                         color='orange', stat="density")
            axes[i].set_xlabel('Error in calibrated model predictions')
            mean_val = np.mean(errors[:,i])
            axes[i].axvline(mean_val, color='blue', linestyle='--')

            axes[i].set_xlim(xmin, xmax)

        plt.tight_layout()

        if dumpfiles:
            plt.savefig(self.odirectory+"/predictions.png")
        if onscreen:
            plt.show()
        plt.close()


    def plotPriorsPosteriors(self, *, onscreen=True, dumpfiles=True):
        """
        Generate a figure illustrating the prior probability distributions
        for the parameters and hyperparameters.

        Parameters
        ----------
        onscreen: if True, plot the figure on the screen
        dumpfiles: if True, write the figure on a file

        Returns
        -------
        None
        """
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()

        fig, axes = plt.subplots(nPHE, 1, figsize=(8, 2*nPHE))
        axes = np.atleast_1d(axes)

        for i in range(nParam):
            xmin = min(posterior[:,i])
            xmax = max(posterior[:,i])
            x_vals = np.linspace(xmin, xmax, 250)
            pdf_vals = self.model.priors[i].pdf(x_vals)
            prior_label = "Prior (" + self.model.priors[i].label + ")"
            axes[i].plot(x_vals, pdf_vals, color='royalblue', label=prior_label)
            sns.histplot(posterior[:, i], bins=30, kde=True, ax=axes[i],
                         color='orange', label='Posterior', stat="density")
            axes[i].legend()
            axes[i].set_title(f"Parameter: {labels[i]}")

        for i in range(nHyper):
            xmin = min(posterior[:,nParam+i])
            xmax = max(posterior[:,nParam+i])
            x_vals = np.linspace(xmin, xmax, 250)
            pdf_vals = self.hyperPriors[i].pdf(x_vals)
            prior_label = "Prior (" + self.hyperPriors[i].label + ")"
            axes[nParam+i].plot(x_vals, pdf_vals, color='blue', label=prior_label)
            sns.histplot(posterior[:,nParam+i], bins=30, kde=True, ax=axes[nParam+i],
                         color='orange', label='Posterior', stat="density")
            axes[nParam+i].legend()
            axes[nParam+i].set_title(f"Parameter: {labels[nParam+i]}")

        if nExp == 1:
            xmin = min(posterior[:,-1])
            xmax = max(posterior[:,-1])
            x_vals = np.linspace(xmin, xmax, 250)
            pdf_vals = self.expPrior.pdf(x_vals)
            prior_label = "Prior (" + self.expPrior.label + ")"
            axes[-1].plot(x_vals, pdf_vals, color='blue', label=prior_label)
            sns.histplot(posterior[:,-1], bins=30, kde=True, ax=axes[-1],
                         color='orange', label='Posterior', stat="density")
            axes[-1].legend()
            axes[-1].set_title(f"Parameter: {labels[-1]}")

        plt.tight_layout()

        if dumpfiles:
            plt.savefig(self.odirectory+"/priors.png")
        if onscreen:
            plt.show()
        plt.close()


    def plotTrace(self, *, onscreen=True, dumpfiles=True):
        """
        Creates a plot with the MCMC sample trace. It thins the number
        of points to NPOINTS, so as to be able to distinguish the trace.

        Parameters
        ----------
        onscreen: if True, plot the figure on the screen
        dumpfiles: if True, write the figure on a file

        Returns
        -------
        None
        """
        NPOINTS = 5000
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()

        fig, ax = plt.subplots(nrows=nPHE, ncols=1, figsize=(8, 2*nPHE))
        ax = np.atleast_1d(ax)

        numpoints = len(posterior)

        if numpoints > NPOINTS:
            indices = np.linspace(0, numpoints - 1, NPOINTS, dtype=int)
        else:
            indices = np.linspace(0, numpoints - 1, numpoints, dtype=int)

        for i in range(nPHE):
            pp = posterior[:,i]
            ax[i].plot(indices, pp[indices], "orange", alpha=0.5)
            ax[i].set_xlim(0, len(posterior))
            ax[i].set_ylabel(f"{labels[i]}")
            ax[-1].set_xlabel("Step number")

        if dumpfiles:
            plt.savefig(self.odirectory+"/trace.png")
        if onscreen:
            plt.show()
        plt.close()


    def plotCorner(self, *, onscreen=True, dumpfiles=True):
        """
        Creates a plot with the pairwise and single variable
        marginalized probability distributions of parameters
        and hyperparameters. Show the MAP and mean.

        Parameters
        ----------
        onscreen: if True, plot the figure on the screen
        dumpfiles: if True, write the figure on a file

        Returns
        -------
        None
        """
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels() # + ("log prob",)
        large_value = 1000
        posterior_new = np.nan_to_num(posterior, nan=large_value,
                                      posinf=large_value, neginf=-large_value)
        cl = 0.95
        rang =[(min_val, max_val)
               for min_val, max_val in
               zip(posterior_new.min(axis=0), posterior_new.max(axis=0))]
        fig = corner.corner(posterior_new,
                            labels=labels,
                            range=rang,
                            title_quantiles=[(1-cl)/2, 0.5, 1-(1-cl)/2],
                            bins=2 * math.ceil(math.log2(len(posterior_new))),
                            quantiles=[(1-cl)/2, 0.5, 1-(1-cl)/2],
                            show_titles=True)

        axes = np.array(fig.axes).reshape((nPHE, nPHE))
        res = st.describe(posterior, axis=0)
        MAP = findApproximateMAP(posterior)
        for i in range(nPHE):
            for j in range(nPHE):
                ax = axes[i, j]
                if i == j:
                    ax.axvline(MAP[i], color="royalblue", label="MAP")
                    ax.axvline(res.mean[i], color="coral", label='Mean')
                elif i > j:
                    ax.axvline(x=MAP[j], color="royalblue",label='Mean')
                    ax.axhline(y=MAP[i], color="royalblue",label='Mean')
                    ax.axvline(x=res.mean[j], color="coral", label="Mean")
                    ax.axhline(y=res.mean[i], color="coral", label='Mean')
        plt.legend(loc='best')

        if dumpfiles:
            plt.savefig(self.odirectory+"/corner.png")
        if onscreen:
            plt.show()
        plt.close()


    def plotCorrelations(self, *, onscreen=True, dumpfiles=True):
        """
        Writes a short report on the correlations between variables
        in the log file.

        Parameters
        ----------
        onscreen: if True, plot the figure on the screen
        dumpfiles: if True, write the figure on a file

        Returns
        -------
        None
        """
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()

        large_value = 1000
        posterior_new = np.nan_to_num(posterior, nan=large_value,
                                      posinf=large_value, neginf=-large_value)

        sigma = np.corrcoef(posterior_new, rowvar=False)
        #plt.imshow(sigma, cmap='YlOrRd', interpolation='nearest')
        plt.clf()
        plt.imshow(sigma, cmap='YlOrRd', interpolation='nearest', vmin=-1, vmax=1)
        plt.colorbar(label='Pearson correlation coefficient')
        plt.xticks(ticks=np.arange(nPHE), labels=labels)
        plt.yticks(ticks=np.arange(nPHE), labels=labels)

        if dumpfiles:
            plt.savefig(self.odirectory+"/pearson.png")
        if onscreen:
            plt.show()
        plt.close()


    def predictionError(self):
        """
        Once a model has been calibrated, compute an array of errors
        made comparing the experimental values with the model predictions.

        Parameters
        ----------
        None

        Returns
        -------
        An array of errors of shape nexp x ydim , or None if it can not be calculated
        """
        if not self.usesSymbolicModel:
            return None


        posterior = np.load(self.odirectory + "/samples.npy")
        MAP = findApproximateMAP(posterior)
        nParam = self.getNParam()
        ttest = np.full((self.nExp, len(MAP[:nParam])), MAP[:nParam])

        nout = self.model.getOutputDimension()
        yExp = np.atleast_2d(self.yExp).T
        if nout > 1:
            errors = []
            if self.xSyn is not None:
                if np.shape(self.xExp)[1]>self.model.xdim:
                    xExp = self.remove_task_index(self.xExp, nout)
                    mtheta = self.remove_extrarows(ttest, nout)
                    y = self.model.original_symbolicModel(xExp, mtheta)
                    N = len(y) // nout
                    for i in range(nout):
                        yi = y[i * N: (i + 1) * N, i]  # slice rows and choose according column
                        yi = np.atleast_2d(yi).T
                        yExpi = yExp[i * N: (i + 1) * N, 0]
                else:
                    y = self.model.original_symbolicModel(self.xExp, ttest)
                    N = len(y) // nout
                    for i in range(nout):
                        yi = y[i * N: (i + 1) * N]  # slice rows and choose according column
                        yi = np.atleast_2d(yi).T
                        yExpi = yExp[i * N: (i + 1) * N]

            else:
                xExp = self.remove_task_index(self.xExp, nout)
                mtheta = self.remove_extrarows(ttest, nout)
                y = self.model.original_symbolicModel(xExp, mtheta)
                N = len(y)
                for i in range(nout):
                    yi = y[:,i]  # in form separate columns for each y
                    yExpi = yExp[i * N: (i + 1) * N]
            error = np.abs(yi - yExpi)
            errors.append(error)
            errors = np.stack(errors, axis=1)
        else:
            y = self.model.symbolicModel(self.xExp, ttest)
            errors = np.abs(y - yExp)
        errors = np.squeeze(errors) #shape (N, nout)
        if errors.ndim == 1:
            errors = errors[:, np.newaxis]  # force shape (N, 1)
        return errors


    def printInfo(self):
        """
        Prints a summary of the calibration process in the log file

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.printlog("\n                          A C B I C I")
        self.printlog("                          ===========")
        self.printlog("\nA Configurable BayesIan Calibration and Inference package")
        self.printlog("\nVersion 2.0.1 (Sep 2025) © Fundación IMDEA Materiales (IMDEA Materials Institute), Getafe, Madrid, Spain and")
        self.printlog("\n                           Universidad Politécnica de Madrid (UPM), Madrid, Spain")
        self.printlog("\nDevelopers: Christina Schenk, Ignacio Romero")
        self.printlog("\n\n")
        self.printlog("\nRuntime information")
        self.printlog("  - Machine name:", socket.gethostname())
        self.printlog("  - Username:", os.getlogin())
        dt = datetime.now()
        self.printlog("  - Execution date:", dt.strftime("%Y-%m-%d"))
        self.printlog("  - Execution time:", dt.strftime("%H:%M:%S"))
        self.printlog("\n\n Calibrator information")
        self.printlog("  - Name:", self.name)
        if self.kernel!=None:
            self.printlog("  - Kernel information:")
            with open(self.logfilename, 'a') as f:
                self.kernel.print(f)

        self.printlog("  - Input space dimension:", self.model.getInputDimension())
        self.printlog("  - Output space dimension:", self.model.getOutputDimension())
        self.printlog("  - Parameters to calibrate and prior distribution:")
        for i, pr in enumerate(self.model.priors):
            self.printlog("    + ", self.model.paramLabels[i])
            with open(self.logfilename, 'a') as f:
                pr.print(f)
        if self.getNHyper()>0:
            self.printlog("  - Hyperparameters to calibrate and prior distribution:")
            for i, pr in enumerate(self.hyperPriors):
                self.printlog("    + ", self.hyperLabels[i])
                with open(self.logfilename, 'a') as f:
                    pr.print(f)
        if not self.knownEE:
            self.printlog("  - Experimental error prior probability distribution:")
            with open(self.logfilename, 'a') as f:
                self.expPrior.print(f)
        else:
            self.printlog("  - Known std of experimental error:", self.expSTD)


    def printlog(self, *args, **kwargs):
        """
        This is a wrapper that allows use the command 'print'
        directly dumping on the log file of the calibration.

        Parameters
        ----------
        *args, **kwargs: this is the standard way of
        declaring the arguments for the print function.

        Returns
        -------
        None
        """

        with open(self.logfilename, 'a') as file:
            print(*args, file=file, **kwargs)


    def printReport(self):
        """
        Writes a file with the statistics for the posterior distribution.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        posterior = np.load(self.odirectory+"/samples.npy")
        with open(self.logfilename, 'a') as f:
            printStatistics(self.getAllLabels(), posterior, file=f)

        error = self.predictionError()
        if error is not None:
            self.printlog("\n\nPrediction error statistics:")
            self.printlog("  - Average error in predictions of calibrated model: ", np.mean(error))
            self.printlog("  - Maximum error in predictions of calibrated model: ", np.max(error))
            self.printlog("  - Standard deviation of prediction errors: ", np.std(error))


    def randomize(self):
        """
        Compute random value of vars to calibrate according to prior
        distributions.

        Parameters
        ----------
        Nonen

        Returns
        -------
        Array with random, valid values for the PHE.
        """
        ran = np.zeros(self.getNPHE())

        nparam = self.getNParam()
        for k, pr in enumerate(self.model.priors):
            ran[k] = pr.randomSample()

        for k, pr in enumerate(self.hyperPriors):
            ran[nparam+k] = pr.randomSample()

        if not self.knownEE:
            nhyper = len(self.hyper)
            ran[nparam+nhyper] = self.expPrior.randomSample()

        return ran


    def replaceHyperparameterPrior(self, *, label, prior):
        """
        Replace the prior distribution for a hyperparameter in the
        calibration. All calibrations, when created, assign a
        default prior distribution to all their hyperparameters. The
        user might want to use this function to replace the default
        with a more appropriate one. Careful: the label provided
        to the function has to match one of the existing labels for
        the calibrator hyperparameters.
        Example:
        theCalibrator.replaceHyperparameterPrior(label=r'$\beta_x$',prior=Cauchy(mu=1.0, sigma=0.1))

        Parameters
        ----------
        label: string with the name of the hyperparameter to be replaced.
        prior: prior probability distribution (of ACBICI type)

        Returns
        -------
        None
        """
        for k in range(self.getNHyper()):
            if self.hyperLabels[k] == label:
                self.hyperPriors[k] = prior
                break


    def setDefaultExperimentalSTDPrior(self):
        """
        Set a default prior distribution for the standard deviation
        of the experimental error, itself being a normal variable. A desirable mean
        and std are first calculated in terms of the available experimental
        data. Then, the prior parameters are set so that the selected
        distribution has this mean and std. Note that the prior support must
        be the positive numbers

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        ybar = np.mean(np.abs(self.yExp))
        fMean = 0.1*ybar
        fSTD = 0.1*fMean
        alpha = fMean*fMean/fSTD
        beta = fMean/fSTD
        self.setExperimentalSTDPrior(Gamma(alpha=alpha, beta=beta))
        self.knownEE = False


    def setExperimentalSTDPrior(self, prior):
        """
        All calibrators assume that the experimental measurements have
        a certain error which is Gaussian and has zero mean. With this
        command, the user sets the standard deviation of the Gaussian
        to be a random variable itself, and provides a prior probability
        distribution for it.

        Parameters
        ----------
        prior: prior probability distribution (of ACBICI type)

        Returns
        -------
        None
        """
        self.knownEE = False
        self.expSTD = prior.randomSample()
        self.expPrior = prior


    def setExperimentalSTDValue(self, val):
        """
        All calibrators assume that the experimental measurements have
        a certain error which is Gaussian and has zero mean. With this
        command, the user fixes the standard deviation of the Gaussian.

        Parameters
        ----------
        val: standard deviation of the distribution of the experimental error.

        Returns
        -------
        None
        """
        self.knownEE = True
        self.expSTD = val
        self.expPrior = None


    def storeExperimentalData(self, data):
        """
        This function transfers the experimental data, a numpy array, to the
        calibrator for its later user. The data must have as many rows as
        desired but xdim+1 columns, where xdim is the dimension of the input
        space.
        Saves xExp in (nsamples, xdim) and yExp in (nsamples,) format.

        Parameters
        ----------
        data: numpy array with the (input, output) data from experiments.

        Returns
        -------
        None
        """
        dim = self.model.getInputDimension()
        ydim = self.model.getOutputDimension()
        # Ensure always 2D shape:
        self.xExp = data[:, :dim].reshape(-1, dim)
        if ydim > 1:
            # Extract outputs
            yExp = data[:, dim:dim + ydim]  # Shape: (n_samples, ydim)
            # Expand input data: repeat each x sample `ydim` times and append task index
            self.xExp = np.repeat(self.xExp, ydim, axis=0)  # Shape: (n_samples * ydim, xdim)
            task_indices = np.tile(np.arange(ydim), len(data)).reshape(-1, 1)  # Task indices

            # Append task indices as a new feature
            self.xExp = np.hstack((self.xExp, task_indices))  # Shape: (n_samples * ydim, xdim + 1)

            # Flatten output data to match the expanded input
            self.yExp = yExp.flatten()
        else:
            self.yExp = data[:,dim]
        self.nExp = len(self.xExp)


    def storeSyntheticData(self, data):
        """
        This function transfers the synthetic data, a numpy array, to the
        calibrator for its later user. The data must have as many rows as
        desired but xdim+pdim+1 columns, where xdim is the dimension of the input
        space, pdim is the number of parameters in the model.
        Saves xSyn in (nsamples, xdim) and ySyn in (nsamples,) format.

        Parameters
        ----------
        data: numpy array with the (x_i, theta_i, output_i) from model runs.

        Returns
        -------
        None
        """
        dim = self.model.getInputDimension()
        ydim = self.model.getOutputDimension()

        # Ensure always 2D shape for xSyn and tSyn
        self.xSyn = data[:, :dim].reshape(-1, dim)  # Shape: (n_samples, xdim)

        # Calculate the number of columns for parameters (total columns - input columns - output columns)
        total_columns = data.shape[1]
        output_start_idx = total_columns - ydim

        # Extract the parameters (which come between the inputs and outputs)
        self.tSyn = data[:, dim:output_start_idx].reshape(-1, total_columns - dim - ydim)  # Shape: (n_samples, pdim)

        if ydim > 1:
            # Extract outputs (the last ydim columns)
            ySyn = data[:, output_start_idx:]  # Shape: (n_samples, ydim)

            # Expand input data: repeat each x and theta sample `ydim` times
            self.xSyn = np.repeat(self.xSyn, ydim, axis=0)  # Shape: (n_samples * ydim, xdim)
            self.tSyn = np.repeat(self.tSyn, ydim, axis=0)  # Shape: (n_samples * ydim, pdim)

            # Generate task indices (ensure it is 2D)
            task_indices = np.tile(np.arange(ydim), len(data)).reshape(-1, 1)  # Shape: (n_samples * ydim, 1)

            # Append task indices as a new feature to xSyn
            self.xSyn = np.hstack((self.xSyn, task_indices))  # Shape: (n_samples * ydim, xdim + 1)

            # Flatten output data to match the expanded input
            self.ySyn = ySyn.flatten()  # Shape: (n_samples * ydim,)

        else:
            # If ydim == 1, extract the output from the last column
            self.ySyn = data[:, -1]  # Shape: (n_samples,)
        self.nSyn = len(self.xSyn)


    def storePHE(self, phe):
        """
        Given an array that contains the model parameters, the surrogate
        hyperparameters (if any) and the uknown experimental error (if any),
        store each data in its position.
        """
        nparam = self.getNParam()
        nhyper = self.getNHyper()

        self.model.param = phe[0:nparam]

        if nhyper>0:
            self.hyper = phe[nparam:nparam+nhyper]

        if not self.knownEE:
            self.expSTD = phe[-1]



# -----------------------------------------------------------------------------
#            Type A: Classical calibration
#                    - Inexpensive model
#                    - No discrepancy
#                    - Known experimental error (Gaussian)
# -----------------------------------------------------------------------------
class classicalCalibrator(Calibrator):
    """
    A class that takes care of a classical Bayesian calibration process: given
    an analytical expression (or function) that depends on a controlable input and
    a collection of parameters, finds the best values for the paramters in the sense
    that they explain the experimental results best and are consistent with our
    prior knowledge. The experimental data must have a known experimental error
    assumed to be Gaussian.
    """

    def __init__(self, aModel, *, name=""):
        """
        Constructor

        Parameters
        ----------
        core: an ACBICImodel

        Returns
        -------
        None
        """
        self.model = aModel
        self.name = name
        if not name:
            self.name = f"file_{uuid.uuid4().hex}.txt"
        self.odirectory = self.name + ".out"
        if not os.path.exists(self.odirectory):
            os.makedirs(self.odirectory)
        self.logfilename = self.odirectory + '/acbici.log'
        if os.path.exists(self.logfilename):
            os.remove(self.logfilename)

        if not hasattr(self.model, "original_symbolicModel"):
            self.model.original_symbolicModel = self.model.symbolicModel
        if self.model.getOutputDimension()>1:
            self.model.symbolicModel = lambda xExp, mtheta: self.transformed_model(xExp, mtheta)


    def remove_task_index(self, augmented_xExp, num_tasks):
        """
        Reverse the augmentation process by removing the task index column
        and restoring original xExp.

        Parameters
        ----------
        augmented_xExp : numpy array of shape (n * num_tasks, xdim + 1)
            The augmented data with repeated xExp rows and an additional task index column.
        num_tasks : int
            The number of task repetitions.

        Returns
        -------
        original_xExp : numpy array of shape (n, xdim)
            The restored xExp without task indices.
        """
        # Remove the last column (task index)
        xExp_with_repeats = augmented_xExp[:, :-1]  # Shape: (n * num_tasks, xdim)

        # Since each row was repeated num_tasks times, extract unique rows
        original_xExp = xExp_with_repeats[::num_tasks]  # Take every num_tasks-th row

        return original_xExp


    def remove_extrarows(self, theta, num_tasks):
        """
        Reverse the augmentation process by removing the extra rows and
        restoring the original theta.

        Parameters
        ----------
        augmented_xExp : numpy array of shape (n * num_tasks, xdim + 1)
            The augmented data with repeated xExp rows and an additional task index column.
        num_tasks : int
            The number of task repetitions.

        Returns
        -------
        original_xExp : numpy array of shape (n, xdim)
            The restored xExp without task indices.
        """


        # Since each row was repeated num_tasks times, extract unique rows
        original_xExp = theta[::num_tasks]  # Take every num_tasks-th row

        return original_xExp


    def transformed_model(self, xExp, mtheta):
        num_tasks = self.model.getOutputDimension()
        xExp = self.remove_task_index(xExp, num_tasks)
        mtheta = self.remove_extrarows(mtheta, num_tasks)
        # Evaluate the model
        output_matrix = self.model.original_symbolicModel(xExp, mtheta)  # Shape: (n * num_tasks, ydim)

        # Flatten the output to match the required shape
        reshaped_output = output_matrix.flatten().reshape(-1, 1)  # Shape: (n * num_tasks * ydim, 1)
        return reshaped_output


    def calibrate(self, *, method="mcmc", nsteps=10000, burn=0.2, thin=1, nwalkers=16, nsynthetic=30):
        self.setDefaultHyperparametersPriors()
        self.printInfo()
        self.genericCalibration(method=method, nsteps=nsteps, burn=burn, thin=thin, nwalkers=nwalkers)
        self.printReport()


    def logLikelihood_vect(self):
        """
        Log-likelihood function for known model and normal experimental error.

        This is the log-likelihood of z being sampled from a KOH ansatz
        for which we have x datapoints, and hyperparameters beta, lam, ...

        Parameters
        ----------
        None

        Returns
        -------
        log-likelihood of the KOH model with the value of the parameters
        and hyperparameters
        """
        N = self.nExp
        theModel = self.model
        theta = theModel.param
        s = self.expSTD
        s2 = s*s

        z = self.yExp
        mtheta = np.tile(theta, (N, 1))
        mean = self.model.symbolicModel(self.xExp, mtheta)
        Sigma = s2*np.eye(N)
        ll = self.gaussianLogLikelihood(z, mean, Sigma)

        return ll


    def plot(self, *, compare=True, discrepancy=True, prior=True,
             trace=True, corner=True, pearson=True, prerror=True,
             onscreen=False, dumpfiles=True):
        plt.figure(1)

        if self.model.getOutputDimension()>1:
            compare=False

        if compare and self.model.getInputDimension()==1:
            self.plotCompare(onscreen=onscreen, dumpfiles=dumpfiles)
        elif compare and self.model.getInputDimension()>1:
            self.plotCompare_multix(onscreen=onscreen, dumpfiles=dumpfiles)

        if prior:
            self.plotPriorsPosteriors(onscreen=onscreen, dumpfiles=dumpfiles)

        if trace:
            self.plotTrace(onscreen=onscreen, dumpfiles=dumpfiles)

        if corner:
            self.plotCorner(onscreen=onscreen, dumpfiles=dumpfiles)

        if pearson and self.model.getNParam() > 1:
            self.plotCorrelations(onscreen=onscreen, dumpfiles=dumpfiles)

        if prerror:
            self.plotPredictionErrors(onscreen=onscreen, dumpfiles=dumpfiles)


    def plotCompare(self, *, onscreen=True, dumpfiles=True):
        """
        Creates a plot that compares the provided data and the predictions
        of the calibrated model.

        Parameters
        ----------
        onscreen: if True, plot the figure on the screen
        dumpfiles: if True, write the figure on a file

        Returns
        -------
        None
        """
        # if (self.model.getInputDimension()>1):
        #     return
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()

        nTest = 100
        xtest = np.empty((nTest, 1))
        minTest = np.min(self.xExp)
        maxTest = np.max(self.xExp)
        xtest = np.linspace(minTest, maxTest, nTest)
        MAP = findApproximateMAP(posterior)
        ttest = np.full((nTest, len(MAP[:nParam])), MAP[:nParam])

        xtest = np.atleast_2d(xtest).T if self.model.xdim == 1 else np.atleast_2d(xtest)# Convert x to a 2D array if it's not already
        ttest = np.atleast_2d(ttest)# Convert p to a 2D array if it's not already

        plt.clf()
        plt.plot(self.xExp, self.yExp, 'o', label='Experimental data')
        plt.plot(xtest, self.model.symbolicModel(xtest, ttest),
                 label='Calibrated model', color='red')

        plt.xlabel('x')
        plt.ylabel('y')
        plt.xlim(minTest, maxTest)
        plt.legend(loc='best', framealpha=0.5)

        if dumpfiles:
            plt.savefig(self.odirectory+"/compare.png")
            plt.close()
        if onscreen:
            plt.show()
        plt.close()


    def plotCompare_multix(self, *, onscreen=True, dumpfiles=True):
        """
        Creates a plot for each x dimension that compares the provided data and the predictions
        of the calibrated model.

        Parameters
        ----------
        onscreen: if True, plot the figure on the screen
        dumpfiles: if True, write the figure on a file

        Returns
        -------
        None
        """
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()

        nTest = 100
        xtest = np.empty((nTest, self.model.getInputDimension()))
        for i in range(self.model.getInputDimension()):
            minTest = np.min(self.xExp[:,i])
            maxTest = np.max(self.xExp[:,i])
            xtest[:,i] = np.linspace(minTest, maxTest, nTest)
        MAP = findApproximateMAP(posterior)
        ttest = np.full((nTest, len(MAP[:nParam])), MAP[:nParam])

        xtest = np.atleast_2d(xtest).T if self.model.xdim == 1 else np.atleast_2d(xtest)# Convert x to a 2D array if it's not already
        ttest = np.atleast_2d(ttest)# Convert p to a 2D array if it's not already

        for i in range(self.model.getInputDimension()):
            plt.clf()
            plt.plot(self.xExp[:,i], self.yExp, 'o', label='Experimental data')
            plt.plot(xtest[:,i], self.model.symbolicModel(xtest, ttest),
                     label='Calibrated model', color='red')

            plt.xlabel('x')
            plt.ylabel('y')
            #plt.xlim(minTest, maxTest)
            plt.legend(loc='best', framealpha=0.5)

            if dumpfiles:
                plt.savefig(self.odirectory+"/compare_x"+str(i)+".png")
                plt.close()
            if onscreen:
                plt.show()
            plt.close()


    def setDefaultHyperparametersPriors(self):
        """
        When the user does not provide a prior distribution for the hyperparameters,
        ACBICI will provide the ones in this function. For the classical calibrator,
        only the std of the experimental error needs to be initialized.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.knownEE == False and self.expPrior is None:
            self.setDefaultExperimentalSTDPrior()


    def storeSamples(self, xExperimental, yExperimental):
        """
        Function to store experimental data

        Parameters
        ----------
        xExperimental: x values for experimental datapoints
        yExperimental: y values for experimental datapoints

        Returns
        -------
        None
        """
        self.xExp = xExperimental
        self.yExp = yExperimental
        self.nExp = len(xExperimental)


# -----------------------------------------------------------------------------
#            Type B: expensive calibration
#                    - Expensive model, hence build surrogate
#                    - No discrepancy
# -----------------------------------------------------------------------------
class expensiveCalibrator(Calibrator):
    """
    Features of the calibrator:
       - surrogate gaussian process for the model.
       - experimental error is gaussian, with known variance
    """

    def __init__(self, aModel, *, name="acbiciB", kernel="sqexp"):
        """
        Constructor

        Parameters
        ----------
        aModel: an ACBICI Model
        name: a user name for the calibrator
        kenel: kernel type. Should be "matern32", "matern52", "expo", "ratqua", "sqexpo"

        Returns
        -------
        None
        """
        self.model = aModel
        ydim = self.model.getOutputDimension()
        if ydim>1:
            self.kernel = MultiTask()
        elif kernel == "matern32":
            self.kernel = Matern32()
        elif kernel == "matern52":
            self.kernel = Matern52()
        elif kernel == "expo":
            self.kernel = Expo()
        elif kernel == "ratquad":
            self.kernel = RatQuad()
        else:
            self.kernel = SqExpo()
        self.ydim = ydim
        self.name = name
        if not name:
            self.name = f"file_{uuid.uuid4().hex}.txt"
        self.odirectory = self.name + ".out"
        if not os.path.exists(self.odirectory):
            os.makedirs(self.odirectory)
        self.logfilename = self.odirectory + '/acbici.log'
        if os.path.exists(self.logfilename):
            os.remove(self.logfilename)

        if not hasattr(self.model, "original_symbolicModel"):
            self.model.original_symbolicModel = self.model.symbolicModel

        func = getattr(aModel.__class__, 'symbolicModel', None)
        empty = is_function_effectively_empty(func)
        if empty:
            self.usesSymbolicModel = False


        self.addHyperparameter(r'$\beta_x$',   None)
        self.addHyperparameter(r'$\beta_t$',   None)
        self.addHyperparameter(r'$\lambda_x$', None)


    def getOutputDimension(self):
        """
        Returns the dimension of the output variables of the model = number of tasks.

        Parameters
        ----------
        None

        Returns
        -------
        The dimension
        """
        return self.ydim


    def calibrate(self, *, method="mcmc", nsteps=10000, burn=0.2, thin=1, nwalkers=16, nsynthetic=30):
        if self.nSyn<1:
            self.generateSyntheticData(npoints=nsynthetic)
            sd = np.loadtxt(self.odirectory+"/synthetic.dat")
            self.storeSyntheticData(sd)

        N = self.nExp
        M = self.nSyn
        self.Sigma = np.zeros((N+M,N+M))

        self.setDefaultHyperparametersPriors()
        self.printInfo()
        self.genericCalibration(method=method, nsteps=nsteps, burn=burn, thin=thin,
                                nwalkers=nwalkers)
        self.printReport()


    def covx(self, x1, x2):
        """
        Computes the value of the covariance matrix for two arrays of
        input_data + parameters. The two arrays x1, x2 could be the same one.

        Parameters
        ----------
        x1: an numpy array of input points. Each row must be xdim+pdim size.
        x2: an numpy array of input points. Each row must be xdim+pdim size.

        Returns
        -------
        Covariance matrix.
        """
        beta = self.hyper[0]
        lamb = self.hyper[2]
        ydim = self.model.getOutputDimension()
        k = 0
        if ydim > 1:
            k = 1
        # Ensure x1 and x2 are at least 2-dimensional
        x1 = np.atleast_2d(x1)
        x2 = np.atleast_2d(x2)

        # Initialize the distance matrix
        distance_matrix = np.zeros((x1.shape[0], x2.shape[0]))

        # Calculate the distance matrix using broadcasting
        for i in range(x1.shape[1]-k):
            distance_matrix += abs(np.subtract.outer(x1[:, i], x2[:, i]))**2
        distance_matrix = np.sqrt(distance_matrix)
        return self.kernel(distance_matrix, lamb, beta, x1, x2)


    def covt(self, t1, t2):
        """
        Computes the vallue of the covariance matrix for two arrays of synthetic
        data. The two arrays could be the same.

        Parameters
        ----------
        t1: an numpy array of input points. Each row must be xdim+pdim size.
        t2: an numpy array of input points. Each row must be xdim+pdim size.

        Returns
        -------
        Covariance matrix.
        """
        betat = self.hyper[1]
        lamb = self.hyper[2]

        # Ensure x1 and x2 are at least 2-dimensional
        t1 = np.atleast_2d(t1)
        t2 = np.atleast_2d(t2)

        # Initialize the distance matrix
        distance_matrix = np.zeros((t1.shape[0], t2.shape[0]))
        # Calculate the distance matrix using broadcasting
        for i in range(t1.shape[1]):
            distance_matrix += abs(np.subtract.outer(t1[:, i], t2[:, i])) ** 2
        distance_matrix = np.sqrt(distance_matrix)
        return self.kernel(distance_matrix, lamb, betat)


    def logLikelihood_vect(self):
        """
        Log-likelihood function for KOH ansatz with GP surrogate for the model.

        This is the log-likelihood of z being sampled from a KOH ansatz
        for which we have x datapoints, and hyperparameters beta, lam, ...

        Parameters
        ----------
        None

        Returns
        -------
        log-likelihood of the expensive model with the value of the parameters
        and hyperparameters
        """
        N = self.nExp
        M = self.nSyn

        theModel = self.model
        thetax = np.tile(theModel.param, (N,1))
        covx = self.covx
        covt = self.covt
        s = self.expSTD
        s2 = s*s

        x = self.xExp
        xt = self.xSyn
        tt = self.tSyn
        Sigma = self.Sigma

        # Block 1,1 (shape NxN)
        Covx_1 = covx(x, x)
        Covt_1 = covt(thetax, thetax)
        Sigma[:N, :N] = Covx_1 * Covt_1
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

        # Prepare zero mean vector and concatenate yExp and ySyn
        zero = np.zeros(N + M)
        z = np.concatenate([self.yExp, self.ySyn])

        # Calculate log likelihood
        ll = self.gaussianLogLikelihood(z, zero, Sigma)
        return ll


    def plot(self, *, compare=True, discrepancy=True, prior=True,
             trace=True, corner=True, pearson=True, prerror=True,
             onscreen=False, dumpfiles=True):
        plt.figure(1)

        if self.model.getOutputDimension()>1:
            compare=False

        if compare and self.model.getInputDimension()==1:
            self.plotCompare(onscreen=onscreen, dumpfiles=dumpfiles)
        elif compare and self.model.getInputDimension()>1:
            self.plotCompare_multix(onscreen=onscreen, dumpfiles=dumpfiles)

        if prior:
            self.plotPriorsPosteriors(onscreen=onscreen, dumpfiles=dumpfiles)

        if trace:
            self.plotTrace(onscreen=onscreen, dumpfiles=dumpfiles)

        if corner:
            self.plotCorner(onscreen=onscreen, dumpfiles=dumpfiles)

        if pearson:
            self.plotCorrelations(onscreen=onscreen, dumpfiles=dumpfiles)

        if prerror:
            self.plotPredictionErrors(onscreen=onscreen, dumpfiles=dumpfiles)


    def plotCompare(self, *, onscreen=False, dumpfiles=True):
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()

        nTest = 100
        xtest = np.empty((nTest, self.model.xdim))
        minTest = np.min(self.xExp)
        maxTest = np.max(self.xExp)
        xtest[:,0] = np.linspace(minTest, maxTest, nTest)
        MAP = findApproximateMAP(posterior)
        ttest = np.full((nTest, len(MAP[:nParam])), MAP[:nParam])


        plt.clf()
        plt.plot(self.xExp, self.yExp, 'o', label='Experimental data')

        if self.usesSymbolicModel:
            plt.plot(xtest, self.model.symbolicModel(xtest, ttest),
                     label='Calibrated model', color='red')

        gpr = expensiveGaussianProcess(self.xExp, self.yExp, self.xSyn, self.tSyn, self.ySyn, self)
        ztest, stdtest = gpr.eval_vect(xtest)
        plt.plot(xtest[:,0], ztest, '-', label='GP', color='orange')
        plt.fill_between(xtest[:,0], ztest.flatten() - stdtest, ztest.flatten() + stdtest,
                         alpha=.5, color='orange')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.xlim(minTest, maxTest)
        plt.legend(loc='best', framealpha=0.5)

        if dumpfiles:
            plt.savefig(self.odirectory+"/compare.png")
            #save gp data:
            # Stack data into columns
            data = np.column_stack([xtest, ztest, stdtest])
            # Define the file path
            file_path = self.odirectory + "/output_data_gp.dat"

            # Save to CSV with column headers
            np.savetxt(file_path, data, delimiter=" ", header="x, map_gp, std_gp", comments='')

        if onscreen:
            plt.show()
        plt.close()


    def plotCompare_multix(self, *, onscreen=False, dumpfiles=True):
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()

        nTest = 100
        xtest = np.empty((nTest, self.model.xdim))
        for i in range(self.model.xdim):
            minTest = np.min(self.xExp[:,i])
            maxTest = np.max(self.xExp[:,i])
            xtest[:,i] = np.linspace(minTest, maxTest, nTest)
        MAP = findApproximateMAP(posterior)
        ttest = np.full((nTest, len(MAP[:nParam])), MAP[:nParam])

        gpr = expensiveGaussianProcess(self.xExp, self.yExp, self.xSyn, self.tSyn, self.ySyn, self)
        ztest, stdtest = gpr.eval_vect(xtest)

        for i in range(self.model.xdim):
            plt.clf()
            plt.plot(self.xExp[:,i], self.yExp, 'o', label='Experimental data')

            if self.usesSymbolicModel:
                plt.plot(xtest[:,i], self.model.symbolicModel(xtest, ttest),
                         label='Calibrated model', color='red')


            plt.plot(xtest[:,i], ztest, '-', label='GP', color='orange')
            plt.fill_between(xtest[:,i], ztest.flatten() - stdtest, ztest.flatten() + stdtest,
                             alpha=.5, color='orange')
            plt.xlabel('x')
            plt.ylabel('y')
            #plt.xlim(minTest, maxTest)
            plt.legend(loc='best', framealpha=0.5)

            if dumpfiles:
                plt.savefig(self.odirectory+"/compare_x"+str(i)+".png")
                # save gp data:
                # Stack data into columns
                data = np.column_stack([xtest, ztest, stdtest])
                # Build x column names depending on number of columns
                x_cols = [f"x{i + 1}" if self.model.xdim > 1 else "x" for i in range(self.model.xdim)]
                # Fixed columns after x
                other_cols = ["map_gp", "std_gp", "map_gp_wdisc", "std_gp_wdisc"]

                header = ", ".join(x_cols + other_cols)
                # Define the file path
                file_path = self.odirectory + "/output_data_gp.dat"
                np.savetxt(file_path, data, delimiter=" ", header=header,
                           comments='')
            if onscreen:
                plt.show()
                plt.close()


    def setDefaultHyperparametersPriors(self):
        """
        When the user does not provide a prior distribution for the hyperparameters,
        ACBICI will provide the ones in this function. For the lengthscale beta, we
        propose to use the average pairwise distance of the data in the numerator; for
        the variance lambda, we use the variance of the output.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.knownEE == False and self.expPrior is None:
            self.setDefaultExperimentalSTDPrior()

        if self.hyperPriors[0] is None:
            d = average_pairwise_distance(self.xExp)
            alpha = 5
            beta = 5/d
            self.replaceHyperparameterPrior(label=r'$\beta_x$', prior=Gamma(alpha=alpha, beta=beta))

        if self.hyperPriors[1] is None:
            d = average_pairwise_distance(self.tSyn)
            alpha = 5
            beta = 5/d
            self.replaceHyperparameterPrior(label=r'$\beta_t$', prior=Gamma(alpha=alpha, beta=beta))

        if self.hyperPriors[2] is None:
            d = np.std(self.yExp)
            alpha = 5
            beta = 5/d
            self.replaceHyperparameterPrior(label=r'$\lambda_x$', prior=Gamma(alpha=alpha, beta=beta))


    def remove_task_index(self, augmented_xExp, num_tasks):
        """
        Reverse the augmentation process by removing the task index column
        and restoring original xExp.

        Parameters
        ----------
        augmented_xExp : numpy array of shape (n * num_tasks, xdim + 1)
            The augmented data with repeated xExp rows and an additional task index column.
        num_tasks : int
            The number of task repetitions.

        Returns
        -------
        original_xExp : numpy array of shape (n, xdim)
            The restored xExp without task indices.
        """
        # Remove the last column (task index)
        xExp_with_repeats = augmented_xExp[:, :-1]  # Shape: (n * num_tasks, xdim)

        # Since each row was repeated num_tasks times, extract unique rows
        original_xExp = xExp_with_repeats[::num_tasks]  # Take every num_tasks-th row

        return original_xExp


    def remove_extrarows(self, theta, num_tasks):
        """
        Reverse the augmentation process by removing the extra rows and
        restoring the original theta.

        Parameters
        ----------
        augmented_xExp : numpy array of shape (n * num_tasks, xdim + 1)
            The augmented data with repeated xExp rows and an additional task index column.
        num_tasks : int
            The number of task repetitions.

        Returns
        -------
        original_xExp : numpy array of shape (n, xdim)
            The restored xExp without task indices.
        """


        # Since each row was repeated num_tasks times, extract unique rows
        original_xExp = theta[::num_tasks]  # Take every num_tasks-th row

        return original_xExp


#-----------------------------------------------------------------------------
#            Type C: Discrepancy calibrator
#                    - Inexpensive model
#                    - Discrepancy
# -----------------------------------------------------------------------------
class discrepancyCalibrator(Calibrator):
    """
    Features of the calibrator:
       - the model is known exactly and it is easy to evaluate.
       - gaussian process for the discrepancy (optional)
       - experimental error is gaussian. Its variance may or may not be known.
    """

    def __init__(self, aModel, *, name="acbiciC", kernel="sqexp"):
        """
        Constructor

        Parameters
        ----------
        core: an ACBICI Model

        Returns
        -------
        None
        """
        self.model = aModel
        ydim = self.model.getOutputDimension()
        if ydim>1:
            self.kernel = MultiTask()
        elif kernel == "matern32":
            self.kernel = Matern32()
        elif kernel == "matern52":
            self.kernel = Matern52()
        elif kernel == "expo":
            self.kernel = Expo()
        elif kernel == "ratquad":
            self.kernel = RatQuad()
        else:
            self.kernel = SqExpo()
        self.ydim = ydim
        self.name = name
        if not name:
            self.name = f"file_{uuid.uuid4().hex}.txt"
        self.odirectory = self.name + ".out"
        if not os.path.exists(self.odirectory):
            os.makedirs(self.odirectory)

        self.logfilename = self.odirectory + '/acibici.log'
        if os.path.exists(self.logfilename):
            os.remove(self.logfilename)

        if not hasattr(self.model, "original_symbolicModel"):
            self.model.original_symbolicModel = self.model.symbolicModel
        if self.model.getOutputDimension()>1:
            self.model.symbolicModel = lambda xExp, mtheta: self.transformed_model(xExp, mtheta)

        self.addHyperparameter(r'$\beta_d$', None)
        self.addHyperparameter(r'$\lambda_d$', None)


    def remove_task_index(self, augmented_xExp, num_tasks):
        """
        Reverse the augmentation process by removing the task index column
        and restoring original xExp.

        Parameters
        ----------
        augmented_xExp : numpy array of shape (n * num_tasks, xdim + 1)
            The augmented data with repeated xExp rows and an additional task index column.
        num_tasks : int
            The number of task repetitions.

        Returns
        -------
        original_xExp : numpy array of shape (n, xdim)
            The restored xExp without task indices.
        """
        # Remove the last column (task index)
        xExp_with_repeats = augmented_xExp[:, :-1]  # Shape: (n * num_tasks, xdim)

        # Since each row was repeated num_tasks times, extract unique rows
        original_xExp = xExp_with_repeats[::num_tasks]  # Take every num_tasks-th row

        return original_xExp


    def remove_extrarows(self, theta, num_tasks):
        """
        Reverse the augmentation process by removing the extra rows and
        restoring the original theta.

        Parameters
        ----------
        augmented_xExp : numpy array of shape (n * num_tasks, xdim + 1)
            The augmented data with repeated xExp rows and an additional task index column.
        num_tasks : int
            The number of task repetitions.

        Returns
        -------
        original_xExp : numpy array of shape (n, xdim)
            The restored xExp without task indices.
        """


        # Since each row was repeated num_tasks times, extract unique rows
        original_xExp = theta[::num_tasks]  # Take every num_tasks-th row

        return original_xExp


    def transformed_model(self, xExp, mtheta):
        num_tasks = self.model.getOutputDimension()
        xExp = self.remove_task_index(xExp, num_tasks)
        mtheta = self.remove_extrarows(mtheta, num_tasks)
        # Evaluate the model
        output_matrix = self.model.original_symbolicModel(xExp, mtheta)  # Shape: (n * num_tasks, ydim)

        # Flatten the output to match the required shape
        reshaped_output = output_matrix.flatten().reshape(-1, 1)  # Shape: (n * num_tasks * ydim, 1)
        return reshaped_output


    def getOutputDimension(self):
        """
        Returns the dimension of the output variables of the model = number of tasks.

        Parameters
        ----------
        None

        Returns
        -------
        The dimension
        """
        return self.ydim


    def calibrate(self, *, method="mcmc", nsteps=10000, burn=0.2, thin=1,
                  nwalkers=16, nsynthetic=30, lambda_x_std=None):
        N = self.nExp
        self.Sigma = np.zeros((N,N))

        self.setDefaultHyperparametersPriors()
        self.printInfo()
        self.genericCalibration(method=method, nsteps=nsteps, burn=burn, thin=thin,
                                nwalkers=nwalkers)
        self.printReport()



    def covd(self, x1, x2):
        """
        Covariance discrepancy kernel for pairs of input vectors.

        Parameters
        ----------
        x1 : first input vector. Dimensions xdim+pdim
        x2 : second input vector. Dimensions xdim+pdim

        Returns
        -------
        Covariance matrix for discrepancy
        """
        betad = self.hyper[0]
        lambd = self.hyper[1]

        ydim = self.model.getOutputDimension()
        k = 0
        if ydim>1:
            k = 1
        # Ensure x1 and x2 are at least 2-dimensional
        x1 = np.atleast_2d(x1)
        x2 = np.atleast_2d(x2)

        # Initialize the distance matrix
        distance_matrix = np.zeros((x1.shape[0], x2.shape[0]))

        # Calculate the distance matrix using broadcasting
        for i in range(x1.shape[1]-k):
            distance_matrix += abs(np.subtract.outer(x1[:, i], x2[:, i]))**2
        distance_matrix = np.sqrt(distance_matrix)

        return self.kernel(distance_matrix, lambd, betad, x1, x2)


    def logLikelihood_vect(self):
        """
        Vectorized version
        Log-likelihood function for KOH ansatz with GP for the discrepancy error.

        This is the log-likelihood of z being sampled from a KOH ansatz
        for which we have x datapoints, and hyperparameters beta, lam, ...

        Parameters
        ----------
        None

        Returns
        -------
        log-likelihood of the KOH model with the value of the parameters and hyperparameters
        """
        N = self.nExp
        x = self.xExp
        y = self.yExp

        theModel = self.model
        thetax = np.tile(theModel.param, (N,1))
        covd = self.covd
        s = self.expSTD
        s2 = s*s

        Sigma = np.zeros((N,N))

        # Block 1,1 (shape NxN)
        Covd_1 = covd(x,x)

        Sigma[:N, :N] = Covd_1
        np.fill_diagonal(Sigma[:N, :N], np.diag(Sigma[:N, :N]) + s2)

        # Calculate log likelihood
        mean = theModel.symbolicModel(x, thetax)
        ll = self.gaussianLogLikelihood(y, mean, Sigma)

        return ll


    def plot(self, *, compare=True, discrepancy=True, prior=True,
             trace=True, corner=True, pearson=True, prerror=True,
             onscreen=False, dumpfiles=True):
        plt.figure(1)

        if self.model.getOutputDimension()>1:
            compare=False
            discrepancy=False

        if compare and self.model.getInputDimension()==1:
            self.plotCompare(onscreen=onscreen, dumpfiles=dumpfiles)
        elif compare and self.model.getInputDimension()>1:
            self.plotCompare_multix(onscreen=onscreen, dumpfiles=dumpfiles)

        if discrepancy and self.model.getInputDimension()==1:
            self.plotDiscrepancy(onscreen=onscreen, dumpfiles=dumpfiles)
        elif discrepancy and self.model.getInputDimension()>1:
            self.plotDiscrepancy_multix(onscreen=onscreen, dumpfiles=dumpfiles)

        if prior:
            self.plotPriorsPosteriors(onscreen=onscreen, dumpfiles=dumpfiles)

        if trace:
            self.plotTrace(onscreen=onscreen, dumpfiles=dumpfiles)

        if corner:
            self.plotCorner(onscreen=onscreen, dumpfiles=dumpfiles)

        if pearson:
            self.plotCorrelations(onscreen=onscreen, dumpfiles=dumpfiles)

        if prerror:
            self.plotPredictionErrors(onscreen=onscreen, dumpfiles=dumpfiles)


    def plotCompare(self, *, onscreen=False, dumpfiles=True):
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()

        nTest = 100
        xtest = np.empty((nTest, self.model.xdim))
        minTest = np.min(self.xExp)
        maxTest = np.max(self.xExp)
        xtest[:,0] = np.linspace(minTest, maxTest, nTest)

        MAP = findApproximateMAP(posterior)
        ttest = np.full((nTest, len(MAP[:nParam])), MAP[:nParam])

        plt.clf()
        plt.plot(self.xExp, self.yExp, 'o', label='Experimental data')
        plt.plot(xtest, self.model.symbolicModel(xtest, ttest),
                 label='Calibrated model', color='red')
        gpr = inexpKOHGaussianProcess(self.xExp, self.yExp, self)
        ztest_disc, stdtest_disc = gpr.eval_vect_withdisc(xtest)
        plt.plot(xtest, ztest_disc, '-', label='W/ discrepancy', color='blue')
        plt.fill_between(xtest[:,0], ztest_disc.flatten() - stdtest_disc, ztest_disc.flatten() + stdtest_disc,
                         alpha=.5, color='blue')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.xlim(minTest, maxTest)
        plt.legend(loc='best', framealpha=0.5)

        if dumpfiles:
            plt.savefig(self.odirectory+"/compare.png")
            # save gp data:
            # Stack data into columns
            data = np.column_stack([xtest, ztest_disc, stdtest_disc])
            # Define the file path
            file_path = self.odirectory + "/output_data_w_gp_disc.dat"

            # Save to CSV with column headers
            np.savetxt(file_path, data, delimiter=" ", header="x, map_wdisc, std_wdisc",
                       comments='')
        if onscreen:
            plt.show()
        plt.close()

    def plotCompare_multix(self, *, onscreen=False, dumpfiles=True):
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()
        MAP = findApproximateMAP(posterior)
        nTest = 100
        ttest = np.full((nTest, len(MAP[:nParam])), MAP[:nParam])

        plt.clf()
        xtest = np.empty((nTest, self.model.xdim))
        for i in range(self.model.getInputDimension()):
            minTest = np.min(self.xExp[:,i])
            maxTest = np.max(self.xExp[:,i])
            xtest[:,i] = np.linspace(minTest, maxTest, nTest)

        gpr = inexpKOHGaussianProcess(self.xExp, self.yExp, self)
        ztest_disc, stdtest_disc = gpr.eval_vect_withdisc(xtest)
        x_dim = self.model.getInputDimension()
        for i in range(x_dim):
            plt.plot(self.xExp[:,i], self.yExp, 'o', label='Experimental data')
            plt.plot(xtest[:,i], self.model.symbolicModel(xtest, ttest),
                     label='Calibrated model', color='red')
            plt.plot(xtest[:,i], ztest_disc, '-', label='W/ discrepancy', color='blue')
            plt.fill_between(xtest[:,i], ztest_disc.flatten() - stdtest_disc, ztest_disc.flatten() + stdtest_disc,
                             alpha=.5, color='blue')
            plt.xlabel('x')
            plt.ylabel('y')
            #plt.xlim(minTest, maxTest)
            plt.legend(loc='best', framealpha=0.5)

            if dumpfiles:
                plt.savefig(self.odirectory+"/compare_x"+str(i)+".png")
                # save gp data:
                # Stack data into columns
                data = np.column_stack([xtest, ztest_disc, stdtest_disc])
                # Define the file path
                file_path = self.odirectory + "/output_data_w_gp_disc.dat"

                # Build x column names depending on number of columns
                x_cols = [f"x{i + 1}" if x_dim > 1 else "x" for i in range(x_dim)]
                # Fixed columns after x
                other_cols = ["map_wdisc", "std_wdisc"]
                header = ", ".join(x_cols + other_cols)
                # Save to CSV with column headers
                np.savetxt(file_path, data, delimiter=" ", header=header,
                           comments='')
            if onscreen:
                plt.show()
            plt.close()


    def plotDiscrepancy(self, *, onscreen=False, dumpfiles=True):
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()
        nTest = 100
        MAP = findApproximateMAP(posterior)
        self.storePHE(MAP)
        gpr = inexpKOHGaussianProcess(self.xExp, self.yExp, self)


        xtest = np.empty((nTest, self.model.xdim))
        minTest = np.min(self.xExp)
        maxTest = np.max(self.xExp)
        xtest[:,0] = np.linspace(minTest, maxTest, nTest)
        ztest, stdtest = gpr.eval_vect(xtest)
        ztest_disc, stdtest_disc = gpr.eval_vect_withdisc(xtest)
        disc = ztest_disc-ztest
        std_disc = stdtest_disc-stdtest
        plt.plot(xtest, disc, label='Model discrepancy', color='green')
        plt.fill_between(xtest[:,0], disc.flatten() - std_disc, disc.flatten() + std_disc,
                         alpha=.2, color='green')
        plt.legend(loc='best', framealpha=0.5)

        if dumpfiles:
            plt.savefig(self.odirectory + "/discrepancy.png")
        if onscreen:
            plt.show()
        plt.close()


    def plotDiscrepancy_multix(self, *, onscreen=False, dumpfiles=True):
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()

        MAP = findApproximateMAP(posterior)
        self.storePHE(MAP)
        gpr = inexpKOHGaussianProcess(self.xExp, self.yExp, self)

        nTest = 100
        xtest = np.empty((nTest, self.model.xdim))
        for i in range(self.model.getInputDimension()):
            minTest = np.min(self.xExp[:,i])
            maxTest = np.max(self.xExp[:,i])
            xtest[:,i] = np.linspace(minTest, maxTest, nTest)

        ztest, stdtest = gpr.eval_vect(xtest)
        ztest_disc, stdtest_disc = gpr.eval_vect_withdisc(xtest)
        disc = ztest_disc-ztest
        std_disc = stdtest_disc-stdtest
        for i in range(self.model.getInputDimension()):
            plt.plot(xtest[:,i], disc, label='Model discrepancy', color='green')
            plt.fill_between(xtest[:,i], disc.flatten() - std_disc, disc.flatten() + std_disc,
                             alpha=.2, color='green')
            plt.legend(loc='best', framealpha=0.5)

            if dumpfiles:
                plt.savefig(self.odirectory + "/discrepancy_x"+str(i)+".png")
            if onscreen:
                plt.show()
            plt.close()


    def setDefaultHyperparametersPriors(self):
        """
        When the user does not provide a prior distribution for the hyperparameters,
        ACBICI will provide the ones in this function. For the lengthscale beta, we
        propose to use the average pairwise distance of the data in the numerator; for
        the variance lambda, we use the variance of the output.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.knownEE == False and self.expPrior is None:
            self.setDefaultExperimentalSTDPrior()

        if self.hyperPriors[0] is None:
            d = average_pairwise_distance(self.xExp)
            alpha = 5
            beta = 5 / d
            self.replaceHyperparameterPrior(label=r'$\beta_d$', prior=Gamma(alpha=alpha, beta=beta))

        if self.hyperPriors[1] is None:
            d = np.std(self.yExp)
            alpha = 5
            beta = 5 / d
            self.replaceHyperparameterPrior(label=r'$\lambda_d$', prior=Gamma(alpha=alpha, beta=beta))


# -----------------------------------------------------------------------------
#            Type D: Kennedy & O'Hagan calibration
#                    - Expensive model, hence build surrogate
#                    - Discrepancy
# -----------------------------------------------------------------------------
class KOHCalibrator(Calibrator):
    """
    KOH model class.
    Features of the calibrator:
    - surrogate gaussian process for the model.
    - gaussian process for the discrepancy (optional)
    - experimental error is gaussian, with known variance
    """

    def __init__(self, aModel, *, name="acbiciD", kernel="sqexp"):
        """
        Initializes a KOH calibrator.

        Parameters
        ----------
        aModel: an ACBICI Model

        Returns
        -------
        None
        """
        self.model = aModel
        ydim = self.model.getOutputDimension()
        if ydim>1:
            self.kernel = MultiTask()
        elif kernel == "matern32":
            self.kernel = Matern32()
        elif kernel == "matern52":
            self.kernel = Matern52()
        elif kernel == "expo":
            self.kernel = Expo()
        elif kernel == "ratquad":
            self.kernel = RatQuad()
        else:
            self.kernel = SqExpo()
        self.ydim = ydim
        self.name = name
        if not name:
            self.name = f"file_{uuid.uuid4().hex}.txt"
        self.odirectory = self.name + ".out"
        if not os.path.exists(self.odirectory):
            os.makedirs(self.odirectory)

        self.logfilename = self.odirectory + '/acbici.log'
        if os.path.exists(self.logfilename):
            os.remove(self.logfilename)

        if not hasattr(self.model, "original_symbolicModel"):
            self.model.original_symbolicModel = self.model.symbolicModel

        func = getattr(aModel.__class__, 'symbolicModel', None)
        empty = is_function_effectively_empty(func)
        if empty:
            self.usesSymbolicModel = False


        self.addHyperparameter(r'$\beta_x$',   None)
        self.addHyperparameter(r'$\beta_t$',   None)
        self.addHyperparameter(r'$\lambda_x$', None)
        self.addHyperparameter(r'$\beta_d$',   None)
        self.addHyperparameter(r'$\lambda_d$', None)


    def remove_task_index(self, augmented_xExp, num_tasks):
        """
        Reverse the augmentation process by removing the task index column
        and restoring original xExp.

        Parameters
        ----------
        augmented_xExp : numpy array of shape (n * num_tasks, xdim + 1)
            The augmented data with repeated xExp rows and an additional task index column.
        num_tasks : int
            The number of task repetitions.

        Returns
        -------
        original_xExp : numpy array of shape (n, xdim)
            The restored xExp without task indices.
        """
        # Remove the last column (task index)
        xExp_with_repeats = augmented_xExp[:, :-1]  # Shape: (n * num_tasks, xdim)

        # Since each row was repeated num_tasks times, extract unique rows
        original_xExp = xExp_with_repeats[::num_tasks]  # Take every num_tasks-th row

        return original_xExp


    def remove_extrarows(self, theta, num_tasks):
        """
        Reverse the augmentation process by removing the extra rows and
        restoring the original theta.

        Parameters
        ----------
        augmented_xExp : numpy array of shape (n * num_tasks, xdim + 1)
            The augmented data with repeated xExp rows and an additional task index column.
        num_tasks : int
            The number of task repetitions.

        Returns
        -------
        original_xExp : numpy array of shape (n, xdim)
            The restored xExp without task indices.
        """


        # Since each row was repeated num_tasks times, extract unique rows
        original_xExp = theta[::num_tasks]  # Take every num_tasks-th row

        return original_xExp


    def getOutputDimension(self):
        """
        Returns the dimension of the output variables of the model = number of tasks.

        Parameters
        ----------
        None

        Returns
        -------
        The dimension
        """
        return self.ydim


    def calibrate(self, *, method="mcmc", nsteps=10000, burn=0.2, thin=1, nwalkers=16, nsynthetic=30):
        # if the uses did not provide synthetic data, generate them
        if self.nSyn<1:
            self.generateSyntheticData()
            sd = np.loadtxt(self.odirectory+"/synthetic.dat")
            self.storeSyntheticData(sd)

        N = self.nExp
        M = self.nSyn
        self.Sigma = np.zeros((N+M,N+M))

        self.setDefaultHyperparametersPriors()
        self.printInfo()
        self.genericCalibration(method=method, nsteps=nsteps, burn=burn, thin=thin,
                                nwalkers=nwalkers)
        self.printReport()


    def covd(self, x1, x2):
        betad = self.hyper[3]
        lambd = self.hyper[4]

        ydim = self.model.getOutputDimension()
        k = 0
        if ydim > 1:
            k = 1
        # Ensure x1 and x2 are at least 2-dimensional
        x1 = np.atleast_2d(x1)
        x2 = np.atleast_2d(x2)

        # Initialize the distance matrix
        distance_matrix = np.zeros((x1.shape[0], x2.shape[0]))

        # Calculate the distance matrix using broadcasting
        for i in range(x1.shape[1]-k):
            distance_matrix += abs(np.subtract.outer(x1[:, i], x2[:, i])) ** 2
        distance_matrix = np.sqrt(distance_matrix)
        return self.kernel(distance_matrix, lambd, betad, x1, x2)


    def covt(self, t1, t2):
        betat = self.hyper[1]
        lamb = self.hyper[2]

        # Ensure x1 and x2 are at least 2-dimensional
        t1 = np.atleast_2d(t1)
        t2 = np.atleast_2d(t2)

        # Initialize the distance matrix
        distance_matrix = np.zeros((t1.shape[0], t2.shape[0]))
        # Calculate the distance matrix using broadcasting
        for i in range(t1.shape[1]):
            distance_matrix += abs(np.subtract.outer(t1[:, i], t2[:, i])) ** 2
        distance_matrix = np.sqrt(distance_matrix)
        return self.kernel(distance_matrix, lamb, betat)


    def covx(self, x1, x2):
        beta = self.hyper[0]
        lamb = self.hyper[2]

        ydim = self.model.getOutputDimension()
        k = 0
        if ydim > 1:
            k = 1
        # Ensure x1 and x2 are at least 2-dimensional
        x1 = np.atleast_2d(x1)
        x2 = np.atleast_2d(x2)

        # Initialize the distance matrix
        distance_matrix = np.zeros((x1.shape[0], x2.shape[0]))
        # Calculate the distance matrix using broadcasting
        for i in range(x1.shape[1]-k):
            distance_matrix += abs(np.subtract.outer(x1[:, i], x2[:, i])) ** 2
        distance_matrix = np.sqrt(distance_matrix)
        return self.kernel(distance_matrix, lamb, beta, x1, x2)


    def logLikelihood_vect(self):
        """
        Log-likelihood function for KOH ansatz with GP surrogates for the model
        and discrepancy.

        This is the log-likelihood of z being sampled from a KOH ansatz
        for which we have x datapoints, and hyperparameters beta, lam, ...

        Parameters
        ----------
        None

        Returns
        -------
        log-likelihood of the expensive model with the value of the parameters
        and hyperparameters
        """
        # Loop through the hyperLabels list and add with values to dict:
        N = self.nExp
        M = self.nSyn

        theModel = self.model

        thetax = np.tile(theModel.param, (N,1))

        covx = self.covx
        covt = self.covt
        covd = self.covd
        s = self.expSTD
        s2 = s*s

        x = self.xExp
        xt = self.xSyn
        tt = self.tSyn
        Sigma = self.Sigma

        # Block 1,1 (shape NxN)
        Covx_1 = covx(x, x)
        Covt_1 = covt(thetax, thetax)
        Covd_1 = covd(x, x)
        Sigma[:N, :N] = Covx_1 * Covt_1 + Covd_1
        np.fill_diagonal(Sigma[:N, :N], np.diag(Sigma[:N, :N]) + s2)

        # Block 1,2 (shape NxM)
        Covx_12 = covx(x, xt)
        Covt_12 = covt(thetax, tt)
        Sigma[:N, N:N+M] = Covx_12*Covt_12

        # Block 2,1 (shape MxN)
        Sigma[N:N+M, :N] = Sigma[:N, N:N+M].T

        # Block 2,2 (shape MxM)
        Covx_2 = covx(xt, xt)
        Covt_2 = covt(tt, tt)
        Sigma[N:N+M, N:N+M] = Covx_2 * Covt_2

        # Prepare zero mean vector and concatenate yExp and ySyn
        zero = np.zeros(N+M)
        z = np.concatenate([self.yExp, self.ySyn])

        # Calculate log likelihood
        ll = self.gaussianLogLikelihood(z, zero, Sigma)

        return ll


    def plotDiscrepancy(self, *, onscreen=False, dumpfiles=True):
        posterior = np.load(self.odirectory+"/samples.npy")

        MAP = findApproximateMAP(posterior)
        self.storePHE(MAP)
        gpr = KOHGaussianProcess(self.xExp, self.yExp, self.xSyn, self.tSyn, self.ySyn, self)

        nTest = 100
        xtest = np.empty((nTest, self.model.xdim))
        minTest = np.min(self.xExp)
        maxTest = np.max(self.xExp)
        xtest[:,0] = np.linspace(minTest, maxTest, nTest)
        ztest, stdtest = gpr.eval_vect(xtest)
        ztest_disc, stdtest_disc = gpr.eval_vect_withdisc(xtest)
        disc = ztest_disc-ztest
        std_disc = stdtest_disc-stdtest
        plt.plot(xtest[:,0], disc, label='Model discrepancy', color='green')
        plt.fill_between(xtest[:,0], disc.flatten()-std_disc, disc.flatten()+std_disc,
                         alpha=.2, color='green')

        plt.legend(loc='best', framealpha=0.5)
        if dumpfiles:
            plt.savefig(self.odirectory + "/discrepancy.png")
        if onscreen:
            plt.show()
        plt.close()


    def plotDiscrepancy_multix(self, *, onscreen=False, dumpfiles=True):
        posterior = np.load(self.odirectory+"/samples.npy")

        MAP = findApproximateMAP(posterior)
        self.storePHE(MAP)
        gpr = KOHGaussianProcess(self.xExp, self.yExp, self.xSyn, self.tSyn, self.ySyn, self)

        nTest = 100
        xtest = np.empty((nTest, self.model.xdim))
        for i in range(self.model.getInputDimension()):
            minTest = np.min(self.xExp[:,i])
            maxTest = np.max(self.xExp[:,i])
            xtest[:,i] = np.linspace(minTest, maxTest, nTest)
        ztest, stdtest = gpr.eval_vect(xtest)
        ztest_disc, stdtest_disc = gpr.eval_vect_withdisc(xtest)
        disc = ztest_disc-ztest
        std_disc = stdtest_disc-stdtest
        for i in range(self.model.getInputDimension()):
            plt.plot(xtest[:,i], disc, label='Model discrepancy', color='green')
            plt.fill_between(xtest[:,i], disc.flatten()-std_disc, disc.flatten()+std_disc,
                         alpha=.2, color='green')

            plt.legend(loc='best', framealpha=0.5)
            if dumpfiles:
                plt.savefig(self.odirectory + "/discrepancy_x"+str(i)+".png")
            if onscreen:
                plt.show()
            plt.close()


    def plotCompare(self, *, onscreen=False, dumpfiles=True):
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()

        MAP = findApproximateMAP(posterior)
        self.storePHE(MAP)
        gpr = KOHGaussianProcess(self.xExp, self.yExp, self.xSyn, self.tSyn, self.ySyn, self)

        nTest = 100
        xtest = np.empty((nTest, self.model.xdim))
        minTest = np.min(self.xExp)
        maxTest = np.max(self.xExp)
        xtest[:,0] = np.linspace(minTest, maxTest, nTest)
        ztest, stdtest = gpr.eval_vect(xtest)
        ztest_disc, stdtest_disc = gpr.eval_vect_withdisc(xtest)
        disc = ztest_disc-ztest
        std_disc = stdtest_disc-stdtest
        ttest = np.full((nTest, len(MAP[:nParam])), MAP[:nParam])


        plt.clf()
        plt.plot(self.xExp, self.yExp, 'o', label='Experimental data')

        if self.usesSymbolicModel:
            plt.plot(xtest, self.model.symbolicModel(xtest, ttest),
                     label='Calibrated model', color="red")

        plt.plot(xtest, ztest_disc, '-', label='GP w/ discrepancy', color='blue')
        plt.plot(xtest, ztest, '-', label='GP w/o discrepancy', color='orange')
        plt.fill_between(xtest[:,0], ztest.flatten() - stdtest, ztest.flatten() + stdtest, alpha=.5, color='orange')
        plt.fill_between(xtest[:,0], ztest_disc.flatten() - stdtest_disc, ztest_disc.flatten() + stdtest_disc,
                         alpha=.5, color='blue')

        plt.legend(loc='best', framealpha=0.5)
        if dumpfiles:
            plt.savefig(self.odirectory + "/compare.png")
            # save gp data:
            # Stack data into columns
            data = np.column_stack([xtest, ztest, stdtest, ztest_disc, stdtest_disc])
            # Define the file path
            file_path = self.odirectory + "/output_data_gp.dat"

            # Save to CSV with column headers
            np.savetxt(file_path, data, delimiter=" ", header="x, map_gp, std_gp, map_gp_wdisc, std_gp_wdisc", comments='')
        if onscreen:
            plt.show()
        plt.close()


    def plotCompare_multix(self, *, onscreen=False, dumpfiles=True):
        posterior = np.load(self.odirectory+"/samples.npy")
        nParam = self.getNParam()
        nHyper = self.getNHyper()
        nExp = 0 if self.knownEE else 1
        nPHE = self.getNPHE()
        labels = self.getAllLabels()

        MAP = findApproximateMAP(posterior)
        self.storePHE(MAP)
        gpr = KOHGaussianProcess(self.xExp, self.yExp, self.xSyn, self.tSyn, self.ySyn, self)

        nTest = 100
        xtest = np.empty((nTest, self.model.xdim))
        for i in range(self.model.getInputDimension()):
            minTest = np.min(self.xExp[:,i])
            maxTest = np.max(self.xExp[:,i])
            xtest[:,i] = np.linspace(minTest, maxTest, nTest)
        ztest, stdtest = gpr.eval_vect(xtest)
        ztest_disc, stdtest_disc = gpr.eval_vect_withdisc(xtest)
        disc = ztest_disc-ztest
        std_disc = stdtest_disc-stdtest
        ttest = np.full((nTest, len(MAP[:nParam])), MAP[:nParam])

        x_dim = self.model.getInputDimension()
        for i in range(x_dim):
            plt.clf()
            plt.plot(self.xExp[:,i], self.yExp, 'o', label='Experimental data')

            if self.usesSymbolicModel:
                plt.plot(xtest[:,i], self.model.symbolicModel(xtest, ttest),
                         label='Calibrated model', color="red")

            plt.plot(xtest[:,i], ztest_disc, '-', label='GP w/ discrepancy', color='blue')
            plt.plot(xtest[:,i], ztest, '-', label='GP w/o discrepancy', color='orange')
            plt.fill_between(xtest[:,i], ztest.flatten() - stdtest, ztest.flatten() + stdtest,
                             alpha=.5, color='orange')
            plt.fill_between(xtest[:,i], ztest_disc.flatten() - stdtest_disc,
                             ztest_disc.flatten() + stdtest_disc,
                             alpha=.5, color='blue')

            plt.legend(loc='best', framealpha=0.5)
            if dumpfiles:
                plt.savefig(self.odirectory + "/compare_x"+str(i)+".png")
                # save gp data:
                # Stack data into columns
                data = np.column_stack([xtest, ztest, stdtest, ztest_disc, stdtest_disc])
                # Define the file path
                file_path = self.odirectory + "/output_data_gp.dat"

                # Save to CSV with column headers
                # Build x column names depending on number of columns
                x_cols = [f"x{i + 1}" if x_dim > 1 else "x" for i in range(x_dim)]
                # Fixed columns after x
                other_cols = ["map_gp", "std_gp", "map_gp_wdisc", "std_gp_wdisc"]

                header = ", ".join(x_cols + other_cols)
                np.savetxt(file_path, data, delimiter=" ", header=header,
                           comments='')
            if onscreen:
                plt.show()
            plt.close()


    def plot(self, *, compare=True, discrepancy=True, prior=True,
             trace=True, corner=True, pearson=True, prerror=True,
             onscreen=False, dumpfiles=True):
        plt.figure(1)

        if self.model.getOutputDimension()>1:
            compare=False
            discrepancy=False

        if compare and self.model.getInputDimension()==1:
            self.plotCompare(onscreen=onscreen, dumpfiles=dumpfiles)
        elif compare and self.model.getInputDimension()>1:
            self.plotCompare_multix(onscreen=onscreen, dumpfiles=dumpfiles)

        if discrepancy and self.model.getInputDimension()==1:
            self.plotDiscrepancy(onscreen=onscreen, dumpfiles=dumpfiles)
        elif discrepancy and self.model.getInputDimension()>1:
            self.plotDiscrepancy_multix(onscreen=onscreen, dumpfiles=dumpfiles)

        if prior:
            self.plotPriorsPosteriors(onscreen=onscreen, dumpfiles=dumpfiles)

        if trace:
            self.plotTrace(onscreen=onscreen, dumpfiles=dumpfiles)

        if corner:
            self.plotCorner(onscreen=onscreen, dumpfiles=dumpfiles)

        if pearson:
            self.plotCorrelations(onscreen=onscreen, dumpfiles=dumpfiles)

        if prerror:
            self.plotPredictionErrors(onscreen=onscreen, dumpfiles=dumpfiles)


    def setDefaultHyperparametersPriors(self):
        """
        When the user does not provide a prior distribution for the hyperparameters,
        ACBICI will provide the ones in this function. For the lengthscale beta, we
        propose to use the average pairwise distance of the data in the numerator; for
        the variance lambda, we use the variance of the output.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.knownEE == False and self.expPrior is None:
            self.setDefaultExperimentalSTDPrior()

        if self.hyperPriors[0] is None:
            d = average_pairwise_distance(self.xExp)
            alpha = 5
            beta = 5/d
            self.replaceHyperparameterPrior(label=r'$\beta_x$', prior=Gamma(alpha=alpha, beta=beta))

        if self.hyperPriors[1] is None:
            d = average_pairwise_distance(self.tSyn)
            alpha = 5
            beta = 5/d
            self.replaceHyperparameterPrior(label=r'$\beta_t$', prior=Gamma(alpha=alpha, beta=beta))

        if self.hyperPriors[2] is None:
            d = np.std(self.yExp)
            alpha = 5
            beta = 5/d
            self.replaceHyperparameterPrior(label=r'$\lambda_x$', prior=Gamma(alpha=alpha, beta=beta))

        if self.hyperPriors[3] is None:
            d = average_pairwise_distance(self.tSyn)
            alpha = 5
            beta = 5/d
            self.replaceHyperparameterPrior(label=r'$\beta_d$', prior=Gamma(alpha=alpha, beta=beta))

        if self.hyperPriors[4] is None:
            d = np.std(self.yExp)
            alpha = 5
            beta = 5/d
            self.replaceHyperparameterPrior(label=r'$\lambda_d$', prior=Gamma(alpha=alpha, beta=beta))
