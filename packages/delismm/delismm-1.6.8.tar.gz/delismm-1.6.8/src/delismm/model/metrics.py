"""
Created on 24.03.2015

@author: freu_se


This module contains error metrics
"""

import numpy as np

from delismm.service.exception import DelisMMError


def checkSamples(sample1, sample2, removeNHighest=0):
    """doc"""

    if not isinstance(sample1, np.ndarray):
        sample1 = np.array(sample1)
    if not isinstance(sample2, np.ndarray):
        sample2 = np.array(sample2)
    if removeNHighest > 0 and removeNHighest >= len(sample1):
        raise DelisMMError("Could not remove n-highest input sample. The sample array is equal or smaller than n.")
    if not isinstance(removeNHighest, int):
        raise DelisMMError("removeNHighest must be of type int")
    if len(sample1) != len(sample2):
        raise DelisMMError("Input samples do not have equal size!")
    return sample1, sample2


def meanSquareError(sample1, sample2, removeNHighest=0):
    """
    .. math::
        MSE=\\frac{1}{n}\\sum_{i=1}^n\\left(\\hat{Y_i} - Y_i\\right)^2
    """
    sample1, sample2 = checkSamples(sample1, sample2, removeNHighest)
    result = (sample1 - sample2) ** 2
    if removeNHighest > 0:
        result = np.sort(result)[: -1 * removeNHighest]
    return result.mean()


def rootMeanSquareError(sample1, sample2, removeNHighest=0):
    """
    .. math::
        RMSE=\\sqrt{\\frac{1}{n}\\sum_{i=1}^n\\left(\\hat{Y_i} - Y_i\\right)^2}
    """
    sample1, sample2 = checkSamples(sample1, sample2, removeNHighest)
    return np.sqrt(meanSquareError(sample1, sample2, removeNHighest))


def relativeMeanSquareError(sample1, sample2, removeNHighest=0):
    """
    .. math::
        MSRE=\\frac{1}{n}\\sum_{i=1}^n\\left(1 - \\frac{min(\\hat{Y_i}, Y_i)}{max(\\hat{Y_i},Y_i)}\\right)^2
    """
    sample1, sample2 = np.abs(checkSamples(sample1, sample2, removeNHighest))
    minByMax = np.array(np.min(np.vstack((sample1, sample2)), 0), dtype=np.float64) / np.max(
        np.vstack((sample1, sample2)), 0
    )
    return meanSquareError(np.ones_like(minByMax), minByMax, removeNHighest)


def relativeRootMeanSquareError(sample1, sample2, removeNHighest=0):
    """
    .. math::
        RMSRE=\\sqrt{\\frac{1}{n}\\sum_{i=1}^n\\left(1 - \\frac{min(\\hat{Y_i}, Y_i)}{max(\\hat{Y_i},Y_i)}\\right)^2}
    """
    sample1, sample2 = np.abs(checkSamples(sample1, sample2, removeNHighest))
    minByMax = np.min(np.array([sample1, sample2]), axis=0) / np.max(np.array([sample1, sample2]), axis=0)
    return rootMeanSquareError(np.ones_like(minByMax), minByMax, removeNHighest)


def normalizedRootMeanSquareError(sample1, sample2):
    """
    .. math::
        NRMSE=\\frac{\\sqrt{\\frac{1}{n}\\sum_{i=1}^n(\\hat{Y_i}-Y_i)^{2}}}{max(abs(Y))}

    :param sample1: sample points used to create the metamodel (Y_i below)
    :param sample2: cross validation values (\\hat{Y_i} below)
    :return: normalized root mean square error
    """
    sample1, sample2 = np.abs(checkSamples(sample1, sample2, removeNHighest=0))
    lenY = len(sample1)
    mse = sum([(sample1[i] - sample2[i]) ** 2 for i in range(lenY)]) / lenY
    max_y = max([abs(sample1[i]) for i in range(lenY)])
    nrmse = np.sqrt(mse) / max_y
    return nrmse


def meanRelativeError(sample1, sample2, removeNHighest=0):
    """
    .. math::
        MRE=\\frac{1}{n}\\sum_{i=1}^n 1 - \\frac{min(\\hat{Y_i}, Y_i)}{max(\\hat{Y_i},Y_i)}

    :param sample1: sample points used to create the metamodel (Y_i below)
    :param sample2: cross validation values (\\hat{Y_i} below)
    :return: mean relative error
    """
    sample1, sample2 = np.abs(checkSamples(sample1, sample2, removeNHighest=0))
    minByMax = np.array(np.min(np.vstack((sample1, sample2)), 0), dtype=np.float64) / np.max(
        np.vstack((sample1, sample2)), 0
    )
    mre = np.mean(minByMax)
    return np.abs(1 - mre)


def r2pressCov(sample1, sample2, removeNHighest=0):
    """Calculates the covariance based r2pres value

    :param sample1: sample points used to create the metamodel (Y_i below)
    :param sample2: cross validation values (\\hat{Y_i} below)

    For a description see
    Forrester p 37

    .. math::
        R^2_{press}=1-(\\frac{cov(s1,s2)}{\\sqrt{var(s1)var(s2)}})^2
    """
    sample1, sample2 = checkSamples(sample1, sample2, removeNHighest)
    cov = np.mean(sample1 * sample2) - np.mean(sample1) * np.mean(sample2)
    r2Corr = (cov / np.sqrt(np.var(sample1) * np.var(sample2))) ** 2
    return r2Corr


def r2press(sample1, sample2, removeNHighest=0):
    """Calculates the r2pres value from Optimus

    :param sample1: sample points used to create the metamodel (Y_i below)
    :param sample2: cross validation values (\\hat{Y_i} below)

    For a description see
    Optimus Theroy Guide Rev10_14 chapter 1.3.3 "Error measures and regression parameters"

    Basically it uses a cross correlation of all sample points used. These are used in the
    SSE. Additionally the SSTOT is calculated to account for the distribution of the samples.

    sum of squared errors:
    .. math::
        SSE=\\sum_{i=1}^n\\left(\\hat{Y_i} - Y_i\\right)^2

    total sum of sqares(sum of squared deviation from the mean value):
    .. math::
        SSTOT=\\sum_{i=1}^n\\left(Y_i - \\bar{Y_i}\\right)^2


    .. math::
        R^2_{press}=1-\\frac{SSE}{SSTOT}
    """
    return 1 - r2pressSub1(sample1, sample2, removeNHighest)


def r2pressSub1(sample1, sample2, removeNHighest=0):
    """substract r2pres from 1

    .. math::
        1 - R^2_{press}=\\frac{SSE}{SSTOT}

    See r2pres for parameter description"""
    sample1, sample2 = checkSamples(sample1, sample2, removeNHighest)
    if removeNHighest > 0:
        # sample1 needs to be reduced as well. Thus it is included in the sorting array
        sampleArray = [(diffs, s1) for diffs, s1 in zip(np.abs(sample1 - sample2), sample1)]
        sampleArray.sort(key=lambda x: x[0])
        sampleArray = np.array(sampleArray[: -1 * removeNHighest]).T
        result, sample1 = sampleArray
    else:
        result = np.abs(sample1 - sample2)
    result = (result**2).mean()
    sse = len(sample1) * result
    sstot = np.sum(np.square(sample1 - np.mean(sample1)))
    r2 = sse / sstot
    return r2


def maxScaledError(sample1, sample2, removeNHighest=None):
    """Calculate the maximum error from cross validation results scaled to the interval size

    :param sample1: sample points used to create the metamodel (Y_i below)
    :param sample2: cross validation values (\\hat{Y_i} below)
    :param removeNHighest: has no effect, just for coherence with all other methods here
    """
    sample1, sample2 = checkSamples(sample1, sample2)
    diffMinMax = np.max(sample1) - np.min(sample1)
    maxCrossValidationDifference = np.array(np.max(np.abs(sample1 - sample2)), np.float64)
    return maxCrossValidationDifference / diffMinMax


def maxScaledErrorLog10(sample1, sample2, removeNHighest=None):
    """calculate log_10(sample1) and log_10(sample2) and then use maxScaledError

    :param sample1: sample points used to create the metamodel (Y_i below)
    :param sample2: cross validation values (\\hat{Y_i} below)
    :param removeNHighest: has no effect, just for coherence with all other methods here
    """
    sample1, sample2 = checkSamples(sample1, sample2)
    return maxScaledError(np.log10(sample1), np.log10(sample2))


def maxRelativeError(sample1, sample2, removeNHighest=None):
    """Calculate the maximum relative error from cross validation results

    .. math::
        MaxRE \\coloneqq max\\left(1 - \\frac{min\\left(\\hat{Y_i}, Y_i\\right)}{max\\left(\\hat{Y_i},Y_i\\right)}\\right)

    :param sample1: sample points used to create the metamodel
    :param sample2: cross validation values
    :param removeNHighest: has no effect, just for coherence with all other methods here
    """
    sample1, sample2 = np.abs(checkSamples(sample1, sample2))
    minByMax = np.array(np.min(np.vstack((sample1, sample2)), 0), dtype=np.float64) / np.max(
        np.vstack((sample1, sample2)), 0
    )
    return np.max(1 - minByMax)


def maxRelativeErrorLog10(sample1, sample2, removeNHighest=None):
    """calculate log_10(sample1) and log_10(sample2) and then use maxRelativeError

    :param sample1: sample points used to create the metamodel
    :param sample2: cross validation values
    :param removeNHighest: has no effect, just for coherence with all other methods here
    """
    sample1, sample2 = checkSamples(sample1, sample2)
    return maxRelativeError(np.log10(sample1), np.log10(sample2))


def maxError(sample1, sample2, removeNHighest=None):
    """Calculate the maximum error from two sets of sample points

    .. math::
        MaxE \\coloneqq max\\left(abs\\left(\\hat{Y_i} - Y_i\\right)\\right)

    :param sample1: sample points used to create the metamodel
    :param sample2: cross validation values
    :param removeNHighest: has no effect, just for coherence with all other methods here
    """
    sample1, sample2 = np.abs(checkSamples(sample1, sample2))
    return np.max(np.abs(sample1 - sample2))


def maxErrorLog10(sample1, sample2, removeNHighest=None):
    """calculate log_10(sample1) and log_10(sample2) and then use maxError

    :param sample1: sample points used to create the metamodel
    :param sample2: cross validation values
    :param removeNHighest: has no effect, just for coherence with all other methods here
    """
    sample1, sample2 = checkSamples(sample1, sample2)
    return maxError(np.log10(sample1), np.log10(sample2))


def correlation(sample1, sample2, removeNHighest=0):
    """calculate log_10(sample1) and log_10(sample2) and then use maxError

    :param sample1: sample points used to create the metamodel
    :param sample2: cross validation values
    :param removeNHighest: has no effect, just for coherence with all other methods here
    """
    sample1, sample2 = checkSamples(sample1, sample2)
    if removeNHighest > 0:
        sample1, sample2 = zip(*[(s1, s2) for _, s1, s2 in sorted(zip(np.abs(sample1 - sample2), sample1, sample2))])
        sample1, sample2 = sample1[: -1 * removeNHighest], sample2[: -1 * removeNHighest]
    return np.corrcoef(sample1, sample2)[0, 1]


def correlationLog10(sample1, sample2, removeNHighest=0):
    """calculate log_10(sample1) and log_10(sample2) and then use maxError

    :param sample1: sample points used to create the metamodel
    :param sample2: cross validation values
    :param removeNHighest: has no effect, just for coherence with all other methods here
    """
    sample1, sample2 = checkSamples(sample1, sample2)
    return correlation(np.log10(sample1), np.log10(sample2))


def bayesianInformationCriterion(sample1, sample2, k):
    """calculate bayesian information criterion for gaussian modeled error disturbances
    https://en.wikipedia.org/wiki/Bayesian_information_criterion#Gaussian_special_case

    :param sample1: sample points used to create the metamodel
    :param sample2: cross validation values
    :param k: number of paramerters that comprise the model
    """
    sample1, sample2 = checkSamples(sample1, sample2)
    n = len(sample1)
    return n * np.log(np.var(sample1 - sample2)) + k * np.log(n)


if __name__ == "__main__":
    filename = "D:\\foo.txt"

    arr = np.loadtxt(filename)

    sample = arr[:, 0]
    hfmm = arr[:, 2]
    vfmm = arr[:, 3]
    n = len(sample)

    b = bayesianInformationCriterion
    print(np.var(sample - hfmm))
    x = sample - hfmm
    print(meanSquareError(x, np.ones_like(x) * x.mean()))
    x = sample - hfmm
    print(np.mean(np.abs(x - x.mean()) ** 2))

    print(b(sample, hfmm, 8 * 2), np.var((sample - hfmm)))
    print(b(sample, vfmm, 8 * 4), np.var((sample - vfmm)))
