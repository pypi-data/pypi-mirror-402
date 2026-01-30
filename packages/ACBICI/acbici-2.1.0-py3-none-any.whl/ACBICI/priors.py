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
Created on Nov 25 2024
Class for probability priors.

@author: Christina Schenk, Ignacio Romero
"""

import sys
import math
import numpy as np
from abc import ABC, abstractmethod
from scipy.stats import cauchy, gamma, halfcauchy, halfnorm, norm, uniform, weibull_min
from math import log

# -----------------------------------------------------------------------------
#                           Abstract prior class
# -----------------------------------------------------------------------------

class prior(ABC):

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.label = ""
        return instance


    def bounds(self):
        """
        Return lower and upper bound values of the distribution. Either
        can be -np.inf or +np.inf

        Parameters
        ----------
        None

        Returns
        -------
        lower: lower bound
        upper: upper bound
        """
        return self.distribution.support()


    def guessInterval(self):
        """
        Return a fair interval for the expected value of the variable

        Parameters
        ----------
        None

        Returns
        -------
        lower: lower bound
        upper: upper bound
        """
        return self.ppf(0.4), self.ppf(0.75)


    def logProbability(self, x):
        """
        Log of the probability density function.

        Parameters
        ----------
        x: scalar at which the log-pdf has to be evaluated.

        Returns
        -------
        logpdf(x)
        """
        return self.distribution.logpdf(x)


    def pdf(self, x):
        """
        Calculate the PDF at the values x.

        Parameters
        ----------
        x: scalar at which the pdf has to be evaluated.

        Returns
        -------
        pdf(x)
        """
        return self.distribution.pdf(x)


    def ppf(self, percentiles):
        """
        Calculate the percentiles point function for input(s)

        Parameters
        ----------
        percentiles: array of scalars of the percentiles that need to be calculated.
                     values should be in [0,1]

        Returns
        -------
        array with the values of the random variable where the percentiles are attained.
        """
        return self.distribution.ppf(percentiles)


    @abstractmethod
    def print(self, file=sys.stdout):
        """
        Write on file information about the probability distribution.
        """
        pass


    def randomSample(self):
        """
        Generate a single sample distributed according to the probability
        distribution of the prior.
        """
        return self.distribution.rvs()


class Cauchy(prior):
    """
    Prior distribution of the class Cauchy with parameters
    mu and sigma

    The PDF is p(x) = 2/(pi sigma) * 1/(1+ (x-mu)^2/sigma^2) for any x
    The distribution is identical to the half-Cauchy, the
    difference being that the random variable might be any real number.

    See:
    https://distribution-explorer.github.io/continuous/cauchy.html
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.cauchy.html#scipy.stats.cauchy
    """

    def __init__(self, *, mu, sigma):
        self.label = "Cauchy"
        self.mu = mu
        self.sigma = sigma
        self.distribution = cauchy(loc=self.mu, scale=self.sigma)
        return


    def print(self, file=sys.stdout):
        print("\tPrior with Cauchy probability distribution", file=file)
        print("\tParameters: mu = {}, sigma = {}".format(self.mu, self.sigma), file=file)



class Gamma(prior):
    """
    Prior distribution of the class Gamma with shape parameter alpha and rate parameter beta.

    The PDF is p(x) = 1/Gamma(alpha) * beta^alpha * x^(alpha-1) * exp[-beta x] with mean
    alpha/beta and variance alpha/beta**2

    See:
    https://distribution-explorer.github.io/continuous/gamma.html
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.gamma.html#scipy.stats.gamma
    """

    def __init__(self, *, alpha, beta):
        self.label = "Gamma"
        self.alpha = alpha
        self.beta = beta
        self.distribution = gamma(a=self.alpha, loc=0.0, scale=1.0/self.beta)
        return


    def print(self, file=sys.stdout):
        print("\tPrior with Gamma probability distribution", file=file)
        print("\tParameters: alpha = {}, beta = {}".format(self.alpha, self.beta), file=file)


class HalfCauchy(prior):
    """
    Prior distribution of the class half-Cauchy with parameters
    mu and sigma

    The PDF is p(x) = 2/(pi sigma) * 1/(1+ (x-mu)^2/sigma^2) for x >= mu

    See https://distribution-explorer.github.io/continuous/halfcauchy.html
    """

    def __init__(self, *, mu, sigma):
        self.label = "Half Cauchy"
        self.mu = mu
        self.sigma = sigma
        self.distribution = halfcauchy(loc=self.mu, scale=self.sigma)
        return


    def print(self, file=sys.stdout):
        print("\tPrior with half-Cauchy probability distribution", file=file)
        print("\tParameters: mu = {}, sigma = {}".format(self.mu, self.sigma), file=file)


class HalfNormal(prior):
    """
    Prior distribution of the class half-normal with parameters
    mu and sigma


    See https://distribution-explorer.github.io/continuous/halfnorm.html
    """

    def __init__(self, *, mu, sigma):
        self.label = "Half normal"
        self.mu = mu
        self.sigma = sigma
        self.distribution = halfnorm.pdf(loc=self.mu, scale=self.sigma)
        return

    def print(self, file=sys.stdout):
        print("\tPrior with half-Cauchy probability distribution", file=file)
        print("\tParameters: mu = {}, sigma = {}".format(self.mu, self.sigma), file=file)


class Normal(prior):
    """
    Prior distribution of the class norm with parameters
    mu and sigma

    The PDF is p(x) = 1/sqrt(2pi sigma^2) * exp[-0.5 (x-mu)^2/sigma^2]

    See:
    https://distribution-explorer.github.io/continuous/norm.html
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html#scipy.stats.norm
    """

    def __init__(self, *, mu, sigma):
        self.label = "Normal"
        self.mu = mu
        self.sigma = sigma
        self.distribution = norm(loc=self.mu, scale=self.sigma)
        return


    def print(self, file=sys.stdout):
        print("\tPrior with normal probability distribution", file=file)
        print("\tParameters: mu = {}, sigma = {}".format(self.mu, self.sigma), file=file)


class Uniform(prior):
    """
    Uniform prior distribution in the interval [a,b]. Probability
    density function is p(x) = 1/(b-a) for a <= x <= b.

    See https://distribution-explorer.github.io/continuous/uniform.html
    """

    def __init__(self, *, a, b):
        self.label = "Uniform"
        self.a = a
        self.b = b
        self.distribution = uniform(loc=self.a, scale=self.b-self.a)
        return


    def print(self, file=sys.stdout):
        print("\tPrior with uniform probability distribution", file=file)
        print("\tProbability support [{},{}]".format(self.a, self.b), file=file)


class Weibull(prior):
    """
    Weibull prior distribution. Probability density function is
    p(x) = 0   x<= 0
    p(x) = (k/lambda) * (x/lambda)^(k-1) * exp(-(x/lambda)^k)

    See https://distribution-explorer.github.io/continuous/weibull.html
    """

    def __init__(self, *, l, k):
        self.label = "Weibull"
        self.lamb = l
        self.k = k
        self.distribution = weibull_min(self.k, loc=0, scale=self.lamb)
        return


    def print(self, file=sys.stdout):
        print("\tPrior with Weibull probability distribution", file=file)
        print("\tlambda: {}, k: {}]".format(self.lamb, self.k), file=file)
