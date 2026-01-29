"""
Created on 13.03.2015

@author: freu_se

Implementing Morris' algorithm(1991) described in Forrester: "Engineering Design via Surrogate Modelling" chapter 1.3.1.

As example please refer to test/test_service/test_screening.py
"""

import numpy as np


def screeningStdMeans(screeningPlanArray, targetSystemValues, xi, l):
    """Generates a variable elementary effect screening plot

    :param screeningPlan: screening plan with values of [0,1] of the shape (k+1*r, k) (built e.g. with screeningPlan()).
        This array corresponds to sampleX.
    :param targetSystemValues: list or np.ndarray with values of target system at each screeningPlan[i]-point
        This array corresponds to sampleY.
    :param xi: elementary effect step length factor
    :param l: number of discrete levels along each dimension

    :return: tuple with 2 entries: List of means, list of standard deviations
    """
    screeningPlanArray = screeningPlanArray.T
    k = screeningPlanArray.shape[1]
    r = screeningPlanArray.shape[0] // (k + 1)
    t = np.array(targetSystemValues)

    d = np.zeros((k, r))
    screeningPlanChunks = np.vsplit(screeningPlanArray, r)
    for chunkIndex, spChunk in enumerate(screeningPlanChunks):
        for index in range(len(spChunk) - 1):
            parameterIndex = np.nonzero(spChunk[index + 1] - spChunk[index])[0][0]
            if (spChunk[index + 1] - spChunk[index])[parameterIndex] < 0:
                parameterDirection = -1
            else:
                parameterDirection = 1
            d[parameterIndex, chunkIndex] = (
                (t[(index + 1) + chunkIndex * (k + 1)] - t[index + chunkIndex * (k + 1)])
                / (xi / (l - 1.0))
                * parameterDirection
            )

    standardDeviations = np.std(d, 1)
    means = np.mean(d, 1)

    meansStar = np.mean(np.abs(d), 1)
    """
    extension from [1]F. Campolongo, J. Cariboni, und A. Saltelli, "An effective screening design for sensitivity analysis of large models", Environmental modelling & software, Bd. 22, Nr. 10, S. 1509-1518, 2007.
    also on page 111 in [1]A. Saltelli u. a., Global Sensitivity Analysis: The Primer, 1. Aufl. Chichester, England; Hoboken, NJ: John Wiley & Sons, 2008.
    """

    return (means, standardDeviations, meansStar)


def plotMeansAndStd(means, standardDeviations, parameterNames):
    """This method creates a plot of the means and standard deviations of a screening"""
    try:
        # these are imports from delis just for output reasons. If you do not have delis installed or in your
        # pythonpath, this method is skipped. You can simply create your own output plot as seen in the book
        from delis.model.geometry.translate import Translation
        from delis.service.geometrywriter import MatplotlibWriter
    except:
        return
    mplWriter = MatplotlibWriter("", "Elementary effects distribution plot", axes="auto")
    mplWriter.scalePlot = False
    mplWriter.printID = True
    mplWriter.textOffset = min([max(means), max(standardDeviations)]) * 1e-2
    mplWriter.marker = "+"
    mplWriter.ax.set_xlabel("Sample Means")
    mplWriter.ax.set_ylabel("Sample Standard Deviations")

    for mean, std, name in zip(means, standardDeviations, parameterNames):
        mplWriter.point(Translation([mean, std, 0], id=name))

    mplWriter.end()
