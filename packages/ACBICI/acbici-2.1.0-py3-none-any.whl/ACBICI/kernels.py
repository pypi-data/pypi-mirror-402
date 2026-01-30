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
Created on Tue Jan 28

@author: Christina Schenk, Ignacio Romero
"""

import numpy as np
import math
from abc import ABC, abstractmethod
import sys

# -----------------------------------------------------------------------------
#                           Abstract kernel class
# -----------------------------------------------------------------------------

class kernel(ABC):

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.label = ""
        return instance


    @abstractmethod
    def evalkernel(self, dist, lamb, beta, x1=None, x2=None):
        """
        Evaluates the kernel for a distance 'dist', given the two hyperparameters
        lambda and beta. All the kernels must be of the form
        k = lambda * f(distance/beta)

        Parameters
        ----------
        dist: distance
        lamb: hyperparameter lambda
        beta: hyperparameter beta

        Returns
        -------
        kernel evaluation
        """
        pass


    @abstractmethod
    def print(self, file=sys.stdout):
        """
        Print information about the kernel on a file

        Parameters
        ----------
        file: filename

        Returns
        -------
        None
        """
        pass


class SqExpo(kernel):
    """
    Squared exponential kernel (RBF or Gaussian Kernel).
    """
    def __init__(self, *, dist=None, lamb=None, beta=None, x1=None, x2=None):
        self.label = "SqExpo"
        self.dist = dist
        self.lamb = lamb
        self.beta = beta
        return


    def evalkernel(self, dist, lamb, beta, x1, x2):
        lamb = lamb if lamb is not None else self.lamb
        beta = beta if beta is not None else self.beta
        dist2 = np.square(dist)
        beta2 = beta*beta
        kernel = np.exp(-0.5*dist2/beta2)  # for multiple betas here /betai2
        return lamb * kernel


    def print(self, file=sys.stdout):
        print("    Squared Exponential Kernel", file=file)


    def __call__(self, dist, lamb, beta, x1=None, x2=None):
        return self.evalkernel(dist, lamb, beta, x1, x2)


class Matern32(kernel):
    """
    Once differentiable Matern kernel.
    """
    def __init__(self, *, dist=None, lamb=None, beta=None, x1=None, x2=None):
        self.label = "Matern32"
        self.dist = dist
        self.lamb = lamb
        self.beta = beta
        return


    def evalkernel(self, dist, lamb, beta):
        lamb = lamb if lamb is not None else self.lamb
        beta = beta if beta is not None else self.beta
        sq3 = 1.732050807568877193
        kernel = (1.0 + sq3 * dist / beta) * np.exp(-sq3 * dist / beta)
        return lamb * kernel


    def __call__(self, dist, lamb, beta, x1=None, x2=None):
        return self.evalkernel(dist, lamb, beta)


    def print(self, file=sys.stdout):
        print("    Matern32 Kernel", file=file)


class Matern52(kernel):
    """
    Twice differentiable Matern kernel.
    """
    def __init__(self, *, dist=None, lamb=None, beta=None, x1=None, x2=None):
        self.label = "Matern52"
        self.dist = dist
        self.lamb = lamb
        self.beta = beta
        return


    def evalkernel(self, dist, lamb, beta):
        lamb = lamb if lamb is not None else self.lamb
        beta = beta if beta is not None else self.beta
        sq5 = 2.236067977499789805
        dist2 = dist*dist
        beta2 = beta*beta
        kernel = (1.0 + sq5 * dist / beta + 5.0 * dist2 / (3.0 * beta2)) * np.exp(-sq5 * dist / beta)
        return lamb * kernel


    def __call__(self, dist, lamb, beta, x1=None, x2=None):
        return self.evalkernel(dist, lamb, beta)


    def print(self, file=sys.stdout):
        print("    Matern52 Kernel", file=file)


class Expo(kernel):
    """
    Exponential kernel. Exponential growth. Rate increases as input increases.
    """
    def __init__(self, *, dist=None, lamb=None, beta=None, x1=None, x2=None):
        self.label = "Expo"
        self.dist = dist
        self.lamb = lamb
        self.beta = beta
        return


    def evalkernel(self, dist, lamb, beta):
        lamb = lamb if lamb is not None else self.lamb
        beta = beta if beta is not None else self.beta
        kernel = np.exp(-dist/beta)
        return lamb * kernel


    def print(self, file=sys.stdout):
        print("    Exponential Kernel", file=file)


    def __call__(self, dist, lamb, beta, x1=None, x2=None):
        return self.evalkernel(dist, lamb, beta)


class RatQuad(kernel):
    """
    Rational quadratic kernel with alpha=1.
    """
    def __init__(self, *, dist=None, lamb=None, beta=None, x1=None, x2=None):
        self.label = "RatQuad"
        self.dist = dist
        self.lamb = lamb
        self.beta = beta
        return


    def evalkernel(self, dist, lamb, beta):
        alpha = 1
        lamb = lamb if lamb is not None else self.lamb
        beta = beta if beta is not None else self.beta
        dist2 = dist*dist
        beta2 = beta*beta
        kernel = (1.0 + dist2 * 0.5 / (alpha*beta2)) ** (-alpha)
        return lamb * kernel


    def print(self, file=sys.stdout):
        print("    Rational Quadratic Kernel with alpha=1", file=file)


    def __call__(self, dist, lamb, beta, x1=None, x2=None):
        return self.evalkernel(dist, lamb, beta)


class MultiTask(kernel):
    """
    Multi Task kernel assuming that tasks independent, just comparing for same task dimension
    0 for different tasks or matern3/2 kernel if same task
    """
    def __init__(self, *, dist=None, lamb=None, beta=None, x1=None, x2=None):
        self.label = "MultiTask"
        self.dist = dist
        self.lamb = lamb
        self.beta = beta
        return


    def evalkernel(self, dist, lamb, beta, x1=None, x2=None):
        lamb = lamb if lamb is not None else self.lamb
        beta = beta if beta is not None else self.beta
        sq3 = 1.732050807568877193
        matern32kernel = lamb * (1.0 + sq3 * dist / beta) * np.exp(-sq3 * dist / beta)
        kernel = matern32kernel

        if x1 is None or x2 is None:
            similkernel = kernel
        else:
            l1 = x1[:, -1]
            l2 = x2[:, -1]

            # Initialize the similarity kernel matrix as all zeros (or ones)
            similkernel = np.zeros((len(l1), len(l2)))

            # Loop through all the last elements of x1 and x2
            for i in range(len(l1)):
                for j in range(len(l2)):
                    if l1[i] == l2[j]:  # If tasks are the same, apply normal kernel, sqexpo or matern
                        similkernel[i, j] = kernel[i, j]
                    else:
                        similkernel[i, j] = 0  # Otherwise, set similarity to 0
        return similkernel



    def print(self, file=sys.stdout):
        print("    Nonstationary Multi Task Kernel", file=file)


    def __call__(self, dist, lamb, beta,  x1=None, x2=None):
        return self.evalkernel(dist, lamb, beta, x1, x2)
