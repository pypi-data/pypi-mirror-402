# -*- coding:utf-8 -*-
# Copyright (C) 2013 Deutsches Zentrum fuer Luft- und Raumfahrt(DLR, German Aerospace Center) <www.dlr.de>
"""
This module contains interfaces to arbitrary target functions.

Generally a target functions is defined by it's actual state which is given by the
actual system parameters. Additionally those parameters have lower and upper bounds
that are handled. Given samples may also be scaled to the bounds or to normalized
samples respectivly.
Lastly a target function must be defined for the system returning the system response
to the actual system state. The system response is returned as a list of arbitrary items.


.. note::
    The target function return value may be extended to return a list of
    system values and graphs in the future.


"""

import itertools
import os
import time
import traceback
from collections import OrderedDict

import numpy as np
from patme.service.logger import log
from patme.service.stringutils import indent

from delismm.service.exception import DelisMMError


class BoundsHandler:
    """This class handles the bounds of a target function. It is capable of converting them
    from the scaled to the non-scaled versions as well as writing and reading them."""

    def __init__(self, lowerBounds, upperBounds):
        """doc"""
        self.bounds = self.getBoundsMatrix(lowerBounds, upperBounds)
        self.lowerBounds = np.array(list(lowerBounds.values()))
        self.upperBounds = np.array(list(upperBounds.values()))

    @staticmethod
    def getBoundsMatrix(lowerBounds, upperBounds):
        """bounds is a list (p x 3), p: number of design variables
        each line is built like this: [ key, lower bound, upper bound]"""
        bounds = []
        for parameterName in lowerBounds.keys():
            if parameterName in upperBounds.keys():
                bounds.append([parameterName, lowerBounds[parameterName], upperBounds[parameterName]])
            else:
                raise DelisMMError("Key in lower bounds is not present in upper bounds. Key: " + str(parameterName))
        return bounds

    @staticmethod
    def getBoundsDicts(bounds):
        """bounds is a list (p x 3), p: number of design variables
        each line is built like this: [ key, lower bound, upper bound]
        returns the bounds as tuple with dictionaries: (lowerBounds, upperBounds)"""
        lowerBounds, upperBounds = OrderedDict([]), OrderedDict()
        for key, lowerBound, upperBound in bounds:
            lowerBounds[key] = lowerBound
            upperBounds[key] = upperBound
        return lowerBounds, upperBounds

    def boundsToFile(self, filename):
        """writes the given bounds and constants to a file. The file will be overwritten without warning!

        :param filename: name of the file and potentially the path where the bounds should be written
        """
        self.boundsToFileStatic(filename, self.bounds, self.customKeywordArgs)

    @staticmethod
    def boundsToFileStaticDict(filename, lowerBounds, upperBounds, constantsDict=None):
        """writes the given bounds and constants to a file. The file will be overwritten without warning!

        :param filename: name of the file and potentially the path where the bounds should be written
        """
        bounds = BoundsHandler.getBoundsMatrix(lowerBounds, upperBounds)
        BoundsHandler.boundsToFileStatic(filename, bounds, constantsDict)

    @staticmethod
    def boundsToFileStatic(filename, bounds, constantsDict):
        """writes the given bounds and constants to a file. The file will be overwritten without warning!

        :param filename: name of the file and potentially the path where the bounds should be written
        """
        if not os.path.exists(os.path.dirname(filename)) and os.path.dirname(filename) != "":
            raise DelisMMError("The directory for the given file does not exist: " + str(os.path.dirname(filename)))
        outString = "parameters:\n" + indent(bounds, delim="  ")
        if constantsDict:
            outString += "constants:\n" + indent(list(constantsDict.items()), delim="  ")
        with open(filename, "w") as f:
            f.write(outString)

    @staticmethod
    def boundsFromFileDict(filename):
        """see boundsFromFile

        :return: tuple of dictionaries: lowerBounds, upperBounds
        """
        bounds, constantValuesDict = BoundsHandler.boundsFromFile(filename)
        lowerBounds, upperBounds = OrderedDict(), OrderedDict()
        for key, lower, upper in bounds:
            lowerBounds[key] = lower
            upperBounds[key] = upper
        return lowerBounds, upperBounds, constantValuesDict

    @staticmethod
    def boundsFromFile(filename):
        """writes the given bounds to a file. The file will be overwritten without warning!

        :param filename: name of the file and potentially the path where the bounds should be written
        :return: bounds is a list (p x 3), p: number of design variables and , cosntantValuesDict as dictionary with constant values
        """
        if not os.path.exists(filename):
            raise DelisMMError("The file to read bounds does not exist: " + str(filename))
        with open(filename, "r") as f:
            lines = f.readlines()
        lineIter = iter(lines)
        bounds = []
        for line in lineIter:
            if line == "\n":
                continue
            if "parameters:" in line:
                continue
            if "constants:" in line:
                break
            key, lower, upper = line.split()
            bounds.append([key, float(lower), float(upper)])
        constantValuesDict = OrderedDict()
        for line in lineIter:
            key, value = line.split()
            if not value.isalpha():
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            if "False" == value:
                value = False
            elif "True" == value:
                value = True
            constantValuesDict[key] = value
        return bounds, constantValuesDict

    def scaleToBounds(self, sampleXNormalized):
        """Method that scales given sample points from a normalized space to real bounds.

        :param sampleX: [n x p] array with samples
        """
        return BoundsHandler.scaleToBoundsStatic(sampleXNormalized, self.lowerBounds, self.upperBounds)

    @staticmethod
    def scaleToBoundsStaticDict(sampleXNormalized, lowerBounds, upperBounds):
        """Method that scales given sample points from a normalized space to real bounds.

        :param sampleX: [n x p] array with samples
        :param lowerBounds: dict with lower bounds of each parameter
        :param upperBounds: dict with upper bounds of each parameter
        """
        return BoundsHandler.scaleToBoundsStatic(
            sampleXNormalized, np.array(list(lowerBounds.values())), np.array(list(upperBounds.values()))
        )

    @staticmethod
    def scaleToBoundsStatic(sampleXNormalized, lowerBoundsArray, upperBoundsArray):
        """Method that scales given sample points from a normalized space to real bounds.

        :param sampleX: [n x p] array with samples
        """
        lowerBoundsArray = np.array(lowerBoundsArray)
        upperBoundsArray = np.array(upperBoundsArray)
        sampleXNormalized = np.array(sampleXNormalized)
        return (lowerBoundsArray + sampleXNormalized.T * (upperBoundsArray - lowerBoundsArray)).T

    def scaleTo01(self, sampleX):
        """Method that scales given sample points to given bounds.

        :param sampleX: [p x n] array with samples
        """
        return ((sampleX.T - self.lowerBounds) / (self.upperBounds - self.lowerBounds)).T

    @staticmethod
    def scaleTo01Static(sampleX, lowerBoundsArray, upperBoundsArray):
        """Method that scales given sample points to given bounds.
        :param lowerBoundsArray: array with lower bounds of each parameter
        :param upperBoundsArray: array with upper bounds of each parameter
        :param sampleX: [n x p] array with samples
        """
        return ((sampleX.T - lowerBoundsArray) / (upperBoundsArray - lowerBoundsArray)).T

    def _getParameterNames(self):
        """doc"""
        return [bound[0] for bound in self.bounds]

    parameterNames = property(fget=_getParameterNames)


class AbstractTargetFunction(BoundsHandler):
    """classdocs"""

    name = "AbstractTargetFunction"

    def __init__(self, lowerBounds, upperBounds, resultNames=None):
        """doc"""
        BoundsHandler.__init__(self, lowerBounds, upperBounds)
        self.p = len(self.bounds)
        self.customKeywordArgs = {}
        """This is a dictionary that may contain custom keyword arguments for the model run.
        With this, one can overwrite the defaults, eg. for panels which are defined in self._getPanel"""

        if not resultNames:
            resultNames = ["resultName"]
        if isinstance(resultNames, str) or not hasattr(resultNames, "__iter__"):
            resultNames = [resultNames]
        self.resultNames = resultNames
        """string or list with the names of the keys returned by self.__call__"""

        self.runDir = None
        self.storeResults = False
        """Flag if the calculation designs and their results should be stored in a file."""
        self.doParallelization = []
        """Parallelization for various purposes can be any combination of "clusterqueue, local, async" or nothing.

        1. "clusterqueue" splits the job according to the actual number of available cluster jobs -1
        2. "local" allows to perform local parallelization according to 3//4 of the number of available cores.
           Local may be combined with clusterqueue, whereas the latter is used first, parallelizing locally to generate
           cluster jobs and performs a second parallelization on the cluster
        3. "async" performs the parallelization locally but uses a defined function to get the maximal number of
           allowed executions. This function is called "getNumberOfNewJobs" and must be
           implemented in the inheriting targetFunc.
           "async" may not be used with "local" at the same time but with clusterqueue.
        """
        self.asyncWaitTime = 0
        """Time in seconds to wait after starting a new async job"""
        self.asyncMaxProcesses = None
        """Maximum number of parallel processes for asynchronous calculations. Must be set in subclasses. """
        self.doRemoteCall = False
        """Flag if the samples should be calculated on the fa-institute cluster"""
        self.allowFailedSample = False
        """In case of an exception raised in the calculation of one sample,
        - the process stops if False
        - continues calculating the next sample if True

        Especially async parallel processes must not fail with an exception since they can create a deadlock.
        If you call samplecalculator.getY() in async mode, this flag should be set to true"""

    def __call__(self, parameters):
        """
        Function that is called to retrieve the actual system response.
        :param parameters: iterable containing the actual system parameters in the same order as self.bounds
        :return: list with system responses
        """
        try:
            result = self._call(np.array(parameters))
        except Exception as e:
            if self.allowFailedSample:
                log.error("\n".join(["Exception raised with this message:", str(e), traceback.format_exc()]))
                result = None
            else:
                raise
        if not isinstance(result, str) and not hasattr(result, "__iter__"):
            # create a list from the result
            result = [result]
        return result

    def _call(self, parameters):
        """see __call__ description

        :return: float or list as system response. The floats will be put in a list in self.__call__!
        """
        raise NotImplementedError("This method must be implemented in a subclass")

    def getNumberOfNewJobs(self):
        """This method is used for asynchronous parallel executions. It returns the number of parallel
        jobs which may vary over time."""
        raise NotImplementedError("This method must be implemented in a subclass")

    def _writeResultToFile(self, result, modelInfoString):
        """method that writes results and the model information to a file.
        Usually the file is kept open during creation of sample points."""
        filename = self.name + "_designs_results.txt"
        if self.runDir is not None:
            filename = os.path.join(self.runDir, filename)
        with open(filename, "a") as f:
            f.write(modelInfoString + "\n")
            f.write("Result: " + str(result) + "\n\n")


class ExampleFunction(AbstractTargetFunction):
    """function from Forrester: engineering design via surrogate modelling (ch. 8.2)"""

    def __init__(self, lowerBounds, upperBounds):
        AbstractTargetFunction.__init__(self, lowerBounds, upperBounds)
        self.name = self.__class__.__name__

    def _call(self, parameters):
        parameters = np.array(parameters)
        return np.sum((6.0 * parameters - 2) ** 2 * np.sin(12 * parameters - 4))


class ExampleFunctionModified(ExampleFunction):
    """See report of Sauerbrei p.38
    function from Forrester: engineering design via surrogate modelling (ch. 8.2)"""

    def __init__(self, lowerBounds, upperBounds):
        ExampleFunction.__init__(self, lowerBounds, upperBounds)

    def _call(self, parameters):
        parameters = np.array(parameters)
        return np.sum(0.5 * ExampleFunction._call(self, parameters) + 10 * (parameters - 0.5) - 5)


class ExampleFunctionAsyncParallelization(ExampleFunction):
    """This is an examplary function for async parallelization"""

    def __init__(self, lowerBounds, upperBounds):
        super().__init__(lowerBounds, upperBounds)
        self.doParallelization = ["async"]
        self.asyncWaitTime = 0.001
        self.asyncMaxProcesses = 4

        self._newJobsScheme = [1, 0]
        """only for testing"""

    def _setNumberOfNewJobsGenerator(self):
        """doc"""
        generator1 = range(3, 0, -1)
        generator2 = itertools.cycle(self._newJobsScheme)
        generator = itertools.chain(generator1, generator2)
        for value in generator:
            yield value

    def getNumberOfNewJobs(self):
        """Creates a generator that returns [3,2,1,1,0,1,0...] as example"""
        if not hasattr(self, "numberOfNewJobsGenerator"):
            self.numberOfNewJobsGenerator = self._setNumberOfNewJobsGenerator()
        return next(self.numberOfNewJobsGenerator)

    def _call(self, parameters):
        """delays the execution randomly in order to test correct order of the samples"""
        time.sleep(np.random.rand() * 0.1)
        return super()._call(parameters)


class ExampleLinearCoupledFunction(AbstractTargetFunction):
    """
    calculates: sum(x_i*i) + sum(x_j*j*x_(j+1)*(j+1))
    where i = 1, .. ,len(self.paramters)
    and   j = 1, .. ,len(self.paramters)-1
    """

    def __init__(self, lowerBounds, upperBounds):
        AbstractTargetFunction.__init__(self, lowerBounds, upperBounds)
        self.name = "ExampleLinearCoupledFunction"

    def _call(self, parameters):
        scaledParams = parameters * np.arange(1, len(parameters) + 1)
        couplingParams = list(zip(scaledParams[:-1], scaledParams[1:]))
        return np.sum(scaledParams) + np.sum(couplingParams)


class ExampleQuadraticCoupledFunction(AbstractTargetFunction):
    """
    calculates: sum(x_i^2*i) + sum(x_j*x_(j+1))
    where i = 1, .. ,len(self.paramters)
    and   j = 1, .. ,len(self.paramters)-1
    """

    def __init__(self, lowerBounds, upperBounds):
        AbstractTargetFunction.__init__(self, lowerBounds, upperBounds)
        self.name = "ExampleQuadraticCoupledFunction"

    def _call(self, parameters):
        scaledParams = parameters * parameters * np.arange(1, len(parameters) + 1)
        couplingParams = list(zip(parameters[:-1], parameters[1:]))
        return np.sum(scaledParams) + np.sum(couplingParams)


class BraninFunction(AbstractTargetFunction):
    """branin function equation 12 of  D. J. J. Toal, "Some considerations regarding the use of multi-fidelity Kriging in the construction of surrogate models,"  2015"""

    def __init__(self, lowerBounds, upperBounds):
        AbstractTargetFunction.__init__(self, lowerBounds, upperBounds)
        self.name = self.__class__.__name__

    def _call(self, parameters):
        x1, x2 = parameters
        return (
            (x2 - 5.1 * x1**2 / 4 / np.pi**2 + 5.0 * x1 / np.pi - 6) ** 2 + 10 * (1 - 1.0 / 8 / np.pi) * np.cos(x1) + 10
        )


class BraninFunctionModified(BraninFunction):
    """branin function modified equation 13 of  D. J. J. Toal, "Some considerations regarding the use of multi-fidelity Kriging in the construction of surrogate models,"  2015"""

    def __init__(self, lowerBounds, upperBounds):
        AbstractTargetFunction.__init__(self, lowerBounds, upperBounds)
        self.name = self.__class__.__name__
        self.a1 = 0.0  # [0,1] is used in the paper

    def _call(self, parameters):
        fBranin = super()._call(parameters)
        x1, x2 = parameters
        return fBranin - (self.a1 + 0.5) * (x2 - 5.1 * x1**2 / 4 / np.pi**2 + 5.0 * x1 / np.pi - 6) ** 2


class JoinedTargetFunction(AbstractTargetFunction):
    """Class for arbitrary target functions. They can be given as function parameter to the constructor"""

    def __init__(self, targetFunction, lowerBounds, upperBounds, name="Joined Target Function"):
        AbstractTargetFunction.__init__(self, lowerBounds, upperBounds)
        self.name = name
        self.targetFunction = targetFunction

    def __call__(self, pointOfInterest):
        """See AbstractKriging for documentation

        returns the value of self.targetFunction()"""
        return self.targetFunction(pointOfInterest)


class RegressionCorrelationCommons:
    """classdoc"""

    def __init__(self, kriging):
        """doc"""
        self.kriging = kriging
        self.name = self.kriging.name + self._name

    def __call__(self, pointOfInterest):
        """See AbstractKriging for documentation

        returns the stochastic correlation part of the kriging model"""
        self.kriging.checkModelCreation()
        return [self._call(pointOfInterest)]

    def _getLowerBounds(self):
        """doc"""
        return self.kriging.lowerBounds

    def _getUpperBounds(self):
        """doc"""
        return self.kriging.upperBounds

    def _getParameterNames(self):
        """doc"""
        return self.kriging.parameterNames

    parameterNames = property(fget=_getParameterNames)
    lowerBounds = property(fget=_getLowerBounds)
    upperBounds = property(fget=_getUpperBounds)


class KrigingMse(RegressionCorrelationCommons):
    """Target function for kriging mse. It is used as kriging(x)+-mse(x). The +- is identified by the flag isUpper"""

    _name = "_regr"

    def __init__(self, kriging, isUpper=True):
        """see base class description

        :param isUpper: flag if the upper or the lower MSE bound should be created
        """
        self._name = "_mse_up" if isUpper else "_mse_low"
        self._isUpper = 1 if isUpper else -1
        RegressionCorrelationCommons.__init__(self, kriging)

    def _call(self, pointOfInterest):
        """See AbstractKriging for documentation

        returns the mse of the kriging model"""
        pointOfInterestNormalized = BoundsHandler.scaleTo01Static(
            np.array(pointOfInterest), self.lowerBounds, self.upperBounds
        )
        mse = self._isUpper * self.kriging.getMSEofPredictor(pointOfInterestNormalized)
        return self.kriging(pointOfInterestNormalized)[0] + mse


class KrigingRegression(RegressionCorrelationCommons):
    """Target function for the regression function of a given kriging model"""

    _name = "_regr"

    def _call(self, pointOfInterest):
        """See AbstractKriging for documentation

        returns the regression part of the kriging model"""
        pointOfInterestNormalized = BoundsHandler.scaleTo01Static(
            np.array(pointOfInterest), self.lowerBounds, self.upperBounds
        )
        return self.kriging.regressionFunction(pointOfInterestNormalized)


class KrigingCorrelation(RegressionCorrelationCommons):
    """Target function for the regression function of a given kriging model"""

    _name = "_corr"

    def _call(self, pointOfInterest):
        """See AbstractKriging for documentation

        returns the stochastic correlation part of the kriging model"""
        pointOfInterestNormalized = BoundsHandler.scaleTo01Static(
            np.array(pointOfInterest), self.lowerBounds, self.upperBounds
        )
        corrVec = self.kriging.getCorrelationVector(pointOfInterestNormalized)
        result = corrVec.T @ self.kriging.v
        return result[0]


class KrigingParallelization:
    """classdoc"""

    def __init__(self, kriging, args, doRemoteCall, runDir=None):
        """doc"""
        self.kriging = kriging
        """the kriging model to be used"""
        self.args = args
        """arguments to the theta optimization function"""
        self.runDir = runDir
        self.doRemoteCall = doRemoteCall
        self.doParallelization = ["clusterqueue"]


class ThetaOptimizerKriging(KrigingParallelization):
    """Target function for the regression function of a given kriging model"""

    name = "krigOpt"

    def __call__(self, pointOfInterest):
        """See AbstractKriging for documentation

        returns the stochastic correlation part of the kriging model"""
        if pointOfInterest != [0]:
            raise DelisMMError("This method should not get any used parameter input")
        return self.kriging._getGlobalOptimum(*self.args)


class CrossValidationValuesCalculatorKriging(KrigingParallelization):
    """Target function for the regression function of a given kriging model"""

    name = "krigCV"

    def __call__(self, pointOfInterest):
        """returns the crossvalidation value at a certain point"""
        return self.kriging.crossValidation(pointOfInterest, *self.args)


class AbsError:
    """Target function for the error function of a given model

    calculates: model2 - model1"""

    def __init__(self, model1, model2):
        """
        :param model1: first model
        :param targetFunction: target function that was used to create the kriging model
        """
        self.model1 = model1
        self.model2 = model2

    def __call__(self, pointOfInterest):
        """See AbstractKriging for documentation"""
        return self.model2(pointOfInterest) - self.model1(pointOfInterest)

    def _getLowerBounds(self):
        """doc"""
        return self.model1.lowerBounds

    def _getUpperBounds(self):
        """doc"""
        return self.model1.upperBounds

    lowerBounds = property(fget=_getLowerBounds)
    upperBounds = property(fget=_getUpperBounds)


class RelError(AbsError):
    """Target function for the error function of a given kriging model

    calculates: 1 - (min(model1,model2) / max(model1,model2))"""

    def __call__(self, pointOfInterest):
        """See AbstractKriging for documentation"""
        s = np.abs(self.model2(pointOfInterest))
        k = np.abs(self.model1(pointOfInterest))
        return 1 - np.min([s, k]) / np.max([s, k])


class ModelDimensionalityTransformer:
    """This class is intended to encapsulate targetfunctions and metamodels in order
    to reduce or increase the number of parameters for a transformation in dimensionality using constants.

    Parameters that are unused(self has more params than model), will be simply omitted.
    Parameters that are added(self has less params than model) to the model, will be introduced as constants.
    Also a mixture of reducing and adding parameters is feasible.

    See test case for examples.
    """

    def __init__(self, model, modelKeys, newModelKeys, constantsValueDict=None):
        """Transforms parameters from newModekKeys --> modelKeys"""
        self.model = model
        differenceKeys = set(modelKeys).difference(newModelKeys)
        if differenceKeys and constantsValueDict is None:
            raise DelisMMError(
                "constantsValueDict must be given as dict since at least one constant values for these keys are reqired: "
                + str(differenceKeys)
            )

        self.parameterTrafo = np.zeros((len(modelKeys), len(newModelKeys)))
        self.parameterConstants = np.zeros((len(modelKeys),))
        for modelKeyIndex, modelKey in enumerate(modelKeys):
            if modelKey in newModelKeys:
                self.parameterTrafo[modelKeyIndex, newModelKeys.index(modelKey)] = 1
            else:
                self.parameterConstants[modelKeyIndex] = constantsValueDict[modelKey]
        print()
        print(modelKeys)
        print(self.parameterTrafo)
        print(self.parameterConstants)

    def __call__(self, parameters):
        """
        Function that is called to retrieve the actual system response.
        :param parameters: iterable containing the actual system parameters in the same order as self.bounds
        :return: float, system response
        """
        parameters = np.array(parameters)
        return [self.model(np.dot(self.parameterTrafo, parameters) + self.parameterConstants)]


if __name__ == "__main__":
    if 0:
        fe = BraninFunction(
            lowerBounds=OrderedDict([("x1", -5.0), ("x2", 0.0)]), upperBounds=OrderedDict([("x1", 10.0), ("x2", 15.0)])
        )
        fc = BraninFunctionModified(
            lowerBounds=OrderedDict([("x1", -5.0), ("x2", 0.0)]), upperBounds=OrderedDict([("x1", 10.0), ("x2", 15.0)])
        )
        print(fe((-np.pi, 12.275)))
        print(fe((np.pi, 2.275)))
        print(fe((9.42478, 2.475)))
        from delismm.model.doe import FullFactorialDesign
        from delismm.model.metrics import correlation, rootMeanSquareError
        from delismm.model.samplecalculator import getY

        doe = FullFactorialDesign(20**2, 2)
        sampleX = fe.scaleToBounds(doe.sampleXNormalized)
        rmses, r2s = [], []
        a1s = np.linspace(0.0, 1.0, 51)
        for a1 in a1s:
            fc.a1 = a1

            sye = getY(sampleX, fe)
            syc = getY(sampleX, fc)
            rmses.append(rootMeanSquareError(sye, syc))
            r2s.append(correlation(sye, syc) ** 2)

        print(indent(zip(rmses, r2s)))

        import matplotlib.pyplot as plt

        fig, ax1 = plt.subplots()
        ax1.plot(a1s, r2s, color="r", label="r2")
        ax1.set_xlabel("A1")
        # Make the y-axis label, ticks and tick labels match the line color.
        ax1.set_ylabel("r2")
        plt.legend(loc="upper left")

        ax2 = ax1.twinx()
        ax2.plot(a1s, rmses, color="b", label="rmse")
        ax2.set_ylabel("RMSE")
        plt.legend()
        plt.show()
