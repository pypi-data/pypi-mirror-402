# Copyright (C) 2013 Deutsches Zentrum fuer Luft- und Raumfahrt(DLR, German Aerospace Center) <www.dlr.de>
"""
This class serves as exemplary controller class for surrogate calculations. Here all general
purpose input parameters are handled.
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from patme.service.logger import log
from patme.service.stringutils import indent

from delismm.model.customsystemfunction import ExampleFunction
from delismm.model.doe import LatinHypercube, MonteCarlo
from delismm.model.metrics import maxError, rootMeanSquareError
from delismm.model.surrogate import Kriging


def runExample(doPlot=False):
    """doc"""
    log.info(f'Surrogate example starting in folder "{os.getcwd()}"')

    lowerBounds = {"testFunction": 0.0}
    upperBounds = {"testFunction": 1.0}

    log.info("Obtain data")
    # ===========================================================================
    # training data
    # ===========================================================================
    targetSystemFunction = ExampleFunction(lowerBounds, upperBounds)
    numberOfSamplePoints = 6
    hypercube = LatinHypercube(numberOfSamplePoints, len(lowerBounds))
    sampleX = targetSystemFunction.scaleToBounds(hypercube.sampleXNormalized)
    sampleY = hypercube.getY(targetSystemFunction)
    # ===========================================================================
    # test data
    # ===========================================================================
    testDoe = MonteCarlo(numberOfSamplePoints, len(lowerBounds))
    sampleXTest = targetSystemFunction.scaleToBounds(testDoe.sampleXNormalized)
    sampleYTest = hypercube.getY(targetSystemFunction)[:, 0]

    log.info("Create Kriging Model")
    kriging = Kriging(
        sampleX,
        sampleY,
        lowerBounds=targetSystemFunction.lowerBounds,
        upperBounds=targetSystemFunction.upperBounds,
    )
    kriging.doRegularizationParameterOpt = False
    kriging.createSurrogateModel()
    log.info(f"kriging documentation:\n{kriging.getKrigingDocumentation()}")

    # =======================================================================
    # error metrics
    # =======================================================================
    errorFunctions = [rootMeanSquareError, maxError]
    # get kriging function values for comparison with sampleYTest
    sampleYTestMM = [kriging(sample)[0] for sample in sampleXTest.T]
    errors = [func(sampleYTest, sampleYTestMM) for func in errorFunctions]
    log.info(f"Error measures:\n{indent([[func.__name__, error] for func, error in zip(errorFunctions, errors)])}")

    if doPlot and len(upperBounds) == 1:
        _, ax0 = plt.subplots(nrows=1)

        # plot target function
        sampleXTest = np.linspace(0.0, 1.0, 100)
        sampleYTest = [targetSystemFunction([poi]) for poi in sampleXTest]
        ax0.plot(sampleXTest, sampleYTest, "k:", label="Target function")

        # plot sample points
        ax0.plot(sampleX[0], sampleY, "ro", label="Sample Points")

        # plot kriging model
        sampleXKriging = np.linspace(0.0, 1.0, 100)
        sampleYKriging = [kriging(poi) for poi in sampleXKriging]
        ax0.plot(sampleXKriging, sampleYKriging, "--", label="Kriging Sample Points")

        ax0.set_title("Metamodel")
        ax0.set_xlabel(kriging.parameterNames[0] + " in []")
        ax0.set_ylabel("Test function value []")
        ax0.legend(
            loc="upper left",
        )
        plt.show()


if __name__ == "__main__":
    runExample(doPlot=True)
    # this will create a doe, sample values, a Metamodel and finally a diagram
