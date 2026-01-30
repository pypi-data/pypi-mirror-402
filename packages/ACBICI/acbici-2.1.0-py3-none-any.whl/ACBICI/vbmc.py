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

import io
import logging
import math
import numpy as np
import os
import sys
from scipy.optimize import minimize
from pyvbmc import VBMC

debug = False

root = logging.getLogger()
pyvbmc_logger = logging.getLogger("pyvbmc")

def _remove_stream_handlers(logger):
    for h in list(logger.handlers):
        if isinstance(h, logging.StreamHandler):
            logger.removeHandler(h)



# Variational Bayes with diagonal Gaussian
class DiagonalVBmc:
    def __init__(self, theCalibrator, n_mc=30):
        self.calibrator = theCalibrator
        self.n_mc = n_mc  # MC samples per ELBO step


    def elbo(self, params):
        """
        Computes the negative of ELBO

        Parameters
        ----------
        params: a numpy array with the initial value of the parameters
                to be calibrated. These include the actual model parameters,
                the hyperparameters of the GP (if any), and the variance
                of the experimental error (if needed)

        Returns
        -------
        Negative ELBO (evidence lower bound)
        """
        dim = self.calibrator.getNPHE()
        mu = params[:dim]
        log_sigma = params[dim:]
        sigma = np.exp(log_sigma)

        elbo_est = 0.0
        for _ in range(self.n_mc):
            eps = np.random.randn(dim)*1e-2
            theta = mu + sigma * eps
            logp = self.calibrator.logPosterior(theta)
            logq = -0.5*np.sum(((theta-mu)/sigma)**2 + 2*log_sigma + np.log(2*np.pi))
            elbo_est += logp - logq

        return -(elbo_est / self.n_mc)


    def fit(self):
        # params are mu, diag(sigma)
        dim = self.calibrator.getNPHE()
        init_params = np.zeros(2 * dim)
        init_params[:dim] = self.calibrator.randomize().reshape((dim,))
        print(f'Starting parameters in fit {init_params}')
        res = minimize(self.elbo, init_params, method="L-BFGS-B")
        mu = res.x[:dim]
        log_sigma = res.x[dim:]
        sigma = np.exp(log_sigma)
        self.mu, self.sigma = mu, sigma
        return mu, sigma


    def sample_posterior(self, n_samples=2000):
        eps = np.random.randn(n_samples, self.calibrator.getNPHE())
        return self.mu + self.sigma * eps


class VBmc:
    """
    A variational Bayes calibrator based on the package pyvbmc
    (https://github.com/acerbilab/pyvbmc)
    """
    def __init__(self, theCalibrator):
        self.calibrator = theCalibrator

        dim = theCalibrator.getNPHE()
        init_params = theCalibrator.randomize().reshape((1,dim))
        lowerB, upperB = theCalibrator.PHEbounds()
        lowerG, upperG = theCalibrator.PHEguess()

        lowerB = lowerB.reshape((1, dim))
        upperB = upperB.reshape((1, dim))
        lowerG = lowerG.reshape((1, dim))
        upperG = upperG.reshape((1, dim))

        for i in range(dim):
            if math.isinf(upperB[0,i]):
                upperB[0,i] = 10.0*upperG[0,i]
            if math.isinf(lowerB[0,i]):
                lowerB[0,i] = 10.0*lowerG[0,i]
            init_params[0,i] = 0.5*(lowerG[0,i] + upperG[0,i])

        if debug:
            print(f'lowerB: {lowerB}')
            print(f'upperB: {upperB}')
            print(f'lowerG: {lowerG}')
            print(f'upperG: {upperG}')
            print(f'init: {init_params}')

        options = {"display": "iter",
                   "log_file_name": theCalibrator.logfilename}

        self.vbmc = VBMC(theCalibrator.logPosterior, init_params,
                         lowerB, upperB, lowerG, upperG,
                         options=options)
        self.vp = 0


    def fit(self):
        """
        This runs variational Bayes with pybvmc. The package does not
        allow to dump results on a file, but not on the screen, so we
        have to deactivate printing to the terminal.
        """
        self.calibrator.printlog('\n\nRunning variational Bayes with pyvbmc...\n')

        _remove_stream_handlers(root)
        _remove_stream_handlers(pyvbmc_logger)

        # Prevent propagation from pyvbmc to root (avoids re-adding console handlers)
        pyvbmc_logger.propagate = False
        # Make sure there’s at least a NullHandler so logging calls don’t warn
        pyvbmc_logger.addHandler(logging.NullHandler())

        self.vp, results = self.vbmc.optimize()
        self.calibrator.printlog('\n\n')


    def sample_posterior(self, n_samples=2000):
        return self.vp.sample(n_samples)[0]
