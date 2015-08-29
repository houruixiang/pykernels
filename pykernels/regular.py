"""
Collection of regular kernel functions, which
are rarely the part of any ML library
"""

__author__ = 'lejlot'

from pykernels.base import Kernel
import numpy as np
from utils import euclidean_dist_matrix


class Exponential(Kernel):
    """
    Exponential kernel, 

        K(x, y) = e^(-||x - y||/(2*s^2))

    where:
        s = sigma
    """

    def __init__(self, sigma=None):
        if sigma is None:
            self._sigma = None
        else:
            self._sigma = 2 * sigma**2

    def _compute(self, data_1, data_2):
        if self._sigma is None:
            # modification of libSVM heuristics
            self._sigma = float(data_1.shape[1])

        dists_sq = euclidean_dist_matrix(data_1, data_2)
        return np.exp(-np.sqrt(dists_sq) / self._sigma)

    def dim(self):
        return np.inf


class Laplacian(Exponential):
    """
    Laplacian kernel, 

        K(x, y) = e^(-||x - y||/s)

    where:
        s = sigma
    """

    def __init__(self, sigma=None):
        self._sigma = sigma



class RationalQuadratic(Kernel):
    """
    Rational quadratic kernel, 

        K(x, y) = 1 - ||x-y||^2/(||x-y||^2+c)

    where:
        c > 0
    """

    def __init__(self, c=1):
        self._c = c

    def _compute(self, data_1, data_2):
        
        dists_sq = euclidean_dist_matrix(data_1, data_2)
        return 1. - (dists_sq / (dists_sq + self._c))

    def dim(self):
        return None #unknown?


class InverseMultiquadratic(Kernel):
    """
    Inverse multiquadratic kernel, 

        K(x, y) = 1 / sqrt(||x-y||^2 + c^2)

    where:
        c > 0

    as defined in:
    "Interpolation of scattered data: Distance matrices and conditionally positive definite functions"
    Charles Micchelli
    Constructive Approximation
    """

    def __init__(self, c=1):
        self._c = c ** 2

    def _compute(self, data_1, data_2):
        
        dists_sq = euclidean_dist_matrix(data_1, data_2)
        return 1. / np.sqrt(dists_sq + self._c)

    def dim(self):
        return np.inf


class Cauchy(Kernel):
    """
    Cauchy kernel, 

        K(x, y) = 1 / (1 + ||x - y||^2 / s ^ 2)

    where:
        s = sigma

    as defined in:
    "A least square kernel machine with box constraints"
    Jayanta Basak
    International Conference on Pattern Recognition 2008
    """

    def __init__(self, sigma=None):
        if sigma is None:
            self._sigma = None
        else:
            self._sigma = sigma**2

    def _compute(self, data_1, data_2):
        if self._sigma is None:
            # modification of libSVM heuristics
            self._sigma = float(data_1.shape[1])

        dists_sq = euclidean_dist_matrix(data_1, data_2)

        return 1 / (1 + dists_sq / self._sigma)

    def dim(self):
        return np.inf



class TStudent(Kernel):
    """
    T-Student kernel, 

        K(x, y) = 1 / (1 + ||x - y||^d)

    where:
        d = degree

    as defined in:
    "Alternative Kernels for Image Recognition"
    Sabri Boughorbel, Jean-Philippe Tarel, Nozha Boujemaa
    INRIA – INRIA Activity Reports – RalyX
    http://ralyx.inria.fr/2004/Raweb/imedia/uid84.html
    """

    def __init__(self, degree=2):
        self._d = degree

    def _compute(self, data_1, data_2):

        dists = np.sqrt(euclidean_dist_matrix(data_1, data_2))
        return 1 / (1 + dists ** self._d)

    def dim(self):
        return None


class ANOVA(Kernel):
    """
    ANOVA kernel, 
        K(x, y) = SUM_k exp( -sigma * (x_k - y_k)^2 )^d

    as defined in

    "Kernel methods in machine learning"
    Thomas Hofmann, Bernhard Scholkopf and Alexander J. Smola
    The Annals of Statistics
    http://www.kernel-machines.org/publications/pdfs/0701907.pdf
    """

    def __init__(self, sigma=1., d=2):
        self._sigma = sigma
        self._d = d

    def _compute(self, data_1, data_2):

        kernel = np.zeros((data_1.shape[0], data_2.shape[0]))

        for d in range(data_1.shape[1]):
            column_1 = data_1[:, d].reshape(-1, 1)
            column_2 = data_2[:, d].reshape(-1, 1)
            kernel += np.exp( -self._sigma * (column_1 - column_2.T)**2 ) ** self._d

        return kernel

    def dim(self):
        return None


from abc import ABCMeta

class PositiveKernel(Kernel):
    """
    Defines kernels which can be only used with positive values
    """
    __metaclass__ = ABCMeta

class AdditiveChi2(PositiveKernel):
    """
    Additive Chi^2 kernel, 
        K(x, y) = SUM_i 2 x_i y_i / (x_i + y_i)

    as defined in

    "Efficient Additive Kernels via Explicit Feature Maps"
    Andrea Vedaldi, Andrew Zisserman
    IEEE TRANSACTIONS ON PATTERN ANALYSIS AND MACHINE INTELLIGENCE
    http://www.robots.ox.ac.uk/~vedaldi/assets/pubs/vedaldi11efficient.pdf
    """

    def _compute(self, data_1, data_2):

        if np.any(data_1 < 0) or np.any(data_2 < 0):
            raise Exception('Additive Chi^2 kernel requires data to be strictly positive!')

        kernel = np.zeros((data_1.shape[0], data_2.shape[0]))

        for d in range(data_1.shape[1]):
            column_1 = data_1[:, d].reshape(-1, 1)
            column_2 = data_2[:, d].reshape(-1, 1)
            kernel += 2 * (column_1 * column_2.T) / (column_1 + column_2.T)

        return kernel

    def dim(self):
        return None

class Chi2(PositiveKernel):
    """
    Chi^2 kernel, 
        K(x, y) = exp( -gamma * SUM_i (x_i - y_i)^2 / (x_i + y_i) )

    as defined in

    "Efficient Additive Kernels via Explicit Feature Maps"
    Andrea Vedaldi, Andrew Zisserman
    IEEE TRANSACTIONS ON PATTERN ANALYSIS AND MACHINE INTELLIGENCE
    http://www.robots.ox.ac.uk/~vedaldi/assets/pubs/vedaldi11efficient.pdf
    """

    def __init__(self, gamma=1.):
        self._gamma = gamma

    def _compute(self, data_1, data_2):

        if np.any(data_1 < 0) or np.any(data_2 < 0):
            raise Exception('Additive Chi^2 kernel requires data to be strictly positive!')

        kernel = np.zeros((data_1.shape[0], data_2.shape[0]))

        for d in range(data_1.shape[1]):
            column_1 = data_1[:, d].reshape(-1, 1)
            column_2 = data_2[:, d].reshape(-1, 1)
            kernel += (column_1 - column_2.T)**2 / (column_1 + column_2.T)

        return np.exp(-self._gamma * kernel)

    def dim(self):
        return None

class Min(PositiveKernel):
    """
    Min kernel (also known as Histogram intersection kernel)
        K(x, y) = SUM_i min(x_i, y_i)

    """

    def _compute(self, data_1, data_2):

        if np.any(data_1 < 0) or np.any(data_2 < 0):
            raise Exception('Min kernel requires data to be strictly positive!')

        kernel = np.zeros((data_1.shape[0], data_2.shape[0]))

        for d in range(data_1.shape[1]):
            column_1 = data_1[:, d].reshape(-1, 1)
            column_2 = data_2[:, d].reshape(-1, 1)
            kernel += np.minimum(column_1, column_2.T)

        return kernel

    def dim(self):
        return None


class GeneralizedHistogramIntersection(PositiveKernel):
    """
    Generalized histogram intersection kernel
        K(x, y) = SUM_i min(|x_i|^alpha, |y_i|^alpha)

    as defined in
    "Generalized histogram intersection kernel for image recognition"
    Sabri Boughorbel, Jean-Philippe Tarel, Nozha Boujemaa
    International Conference on Image Processing (ICIP-2005)
    http://perso.lcpc.fr/tarel.jean-philippe/publis/jpt-icip05.pdf
    """

    def __init__(self, alpha=1.):
        self._alpha = alpha

    def _compute(self, data_1, data_2):

        return Min()._compute(np.abs(data_1)**self._alpha,
                              np.abs(data_2)**self._alpha)

    def dim(self):
        return None



class ConditionalyPositiveDefiniteKernel(Kernel):
    """
    Defines kernels which are only CPD
    """
    __metaclass__ = ABCMeta

class Log(ConditionalyPositiveDefiniteKernel):
    """
    Log kernel
        K(x, y) = -log(||x-y||^d + 1)

    """

    def __init__(self, d=2.):
        self._d = d

    def _compute(self, data_1, data_2):
        return -np.log(euclidean_dist_matrix(data_1, data_2) ** self._d / 2. + 1)

    def dim(self):
        return None


class Power(ConditionalyPositiveDefiniteKernel):
    """
    Power kernel
        K(x, y) = -||x-y||^d

    as defined in:
    "Scale-Invariance of Support Vector Machines based on the Triangular Kernel"
    Hichem Sahbi, Francois Fleuret
    Research report
    https://hal.inria.fr/inria-00071984
    """

    def __init__(self, d=2.):
        self._d = d

    def _compute(self, data_1, data_2):
        return - euclidean_dist_matrix(data_1, data_2) ** self._d / 2.

    def dim(self):
        return None


