# -*- coding:utf-8 -*-
# Copyright (C) 2013 Deutsches Zentrum fuer Luft- und Raumfahrt(DLR, German Aerospace Center) <www.dlr.de>
"""
Created on 28.09.2011

"""

import copy
import os
import pickle
import random
import time
from collections import OrderedDict

import numpy as np
from patme.service.logger import log
from patme.service.stringutils import indent
from scipy import linalg, special
from scipy.optimize import differential_evolution, minimize

from delismm import version as delismmVersion
from delismm.model.apimodels import SurrogateInfo
from delismm.model.customsystemfunction import (
    BoundsHandler,
    CrossValidationValuesCalculatorKriging,
    ThetaOptimizerKriging,
)
from delismm.model.samplecalculator import getY
from delismm.service.exception import DelisMMError


class AbstractSurrogate:
    """Abstract class with interface specifications for surrogate methods"""

    identicSampleXThreshold = 1e-8
    """Threshold for self.removeIdenticSampleX"""

    def __init__(self, sampleX, sampleY, lowerBounds, upperBounds, parameterNames, resultNames):
        """Initialization of surrogate samples

        :param sampleX: numpy array of shape [p,n] (p: number of parameters; n: number of samples)
        :param sampleY: numpy array of shape [n] or [n, x] (x is arbitrary - only x[0] is used)
        :param lowerBounds: numpy array with lower bounds of sample X.
            If None, lowerBounds are calculated from sampleX
        :param upperBounds: numpy array with upper bounds of sample X.
            If None, upperBounds are calculated from sampleX
        :param parameterNames: List with names of each parameter. If None, [p_i] will be used
        :param resultNames: list with the names of the resulting values
        """

        # PARAMETER section ###################################################
        if not isinstance(sampleX, np.ndarray):
            sampleX = np.array(sampleX)
        if lowerBounds is None:
            lowerBounds = np.zeros((sampleX.shape[0],))
        if upperBounds is None:
            upperBounds = np.ones((sampleX.shape[0],))
        self.sampleXNormalized = BoundsHandler.scaleTo01Static(sampleX, lowerBounds, upperBounds)
        self.lowerBounds = lowerBounds
        self.upperBounds = upperBounds
        if parameterNames is None:
            parameterNames = ["p" + str(parameterIndex) for parameterIndex in range(len(self.lowerBounds))]
        self.parameterNames = parameterNames
        self.log10SampleX = np.array([False] * len(parameterNames))
        """Flags if the given sampleX for each parameter are the log10 of the original samples.
        If yes, __call__ will calculate log10 for the respective parameters"""

        # RESULT section ######################################################
        if resultNames is None:
            resultNames = ["resultName"]
        self.resultNames = resultNames
        try:
            sampleY = np.array(sampleY, dtype=np.float64)
        except ValueError:
            # case if sampleY is np.array with ndim==1 but each item contains a list. This happens if there are strings in the previous array
            sampleY = np.array([it[0] for it in sampleY])
        if sampleY.ndim == 2:
            sampleY = sampleY[:, 0]
        elif sampleY.ndim > 2:
            raise DelisMMError("Expected an array of dimension 1 or 2 but got {}".format(sampleY.ndim))
        self.sampleY = np.array(sampleY, dtype=np.float64)
        self.log10SampleY = False
        """Flag if the given sampleY are the log10 of the original samples.
        If yes, __call__ will return power(10, logY)"""
        self.logLevel = log.INFO
        """The loglevel might be changed in some output situations in order to reduce the output"""
        self.name = "surrogate"
        self.removeIdenticSampleX()

    def createSurrogateModel(self):
        """Method that creates the surrogate model. Surrogate settings may be done
        prior to this call"""
        raise NotImplementedError("This method must be implemented in a subclass")

    def targetFunction(self, pointOfInterest):
        """
        Method that evaluates the model on a specific point
        :param pointOfInterest: point to be evaluated
        :return: model return
        """
        raise NotImplementedError("This method must be implemented in a subclass")

    def removeIdenticSampleX(self):
        """Removes samples that identical in respect to a given threshold"""
        newSampleX = []
        newSampleY = []
        for i, samples in enumerate(zip(self.sampleXNormalized.T, self.sampleY)):
            sample1, sampleY = samples
            hasIdenticSample = False
            for j, sample2 in enumerate(self.sampleXNormalized.T[i + 1 :]):
                if np.allclose(sample1, sample2, self.identicSampleXThreshold):
                    hasIdenticSample = True
                    break
            if hasIdenticSample:
                log.warning(
                    "Sample at index {} and {} (zero based counting) are identical. I will remove the first one.".format(
                        i, j + 1 + i
                    )
                )
            else:
                newSampleX.append(sample1)
                newSampleY.append(sampleY)

        if len(newSampleX) != self.sampleXNormalized.shape[1]:
            self.sampleXNormalized = np.array(newSampleX).T
            self.sampleY = np.array(newSampleY)

    def save(self, filename, path=""):
        """saves the surrogate to the file in filename."""
        if path and not os.path.exists(path):
            os.makedirs(path)
        if path:
            filename = os.path.join(path, filename)
        with open(filename, "wb") as f:
            pickle.dump(self, f)
        log.info("Surrogate saved at " + filename)

    @staticmethod
    def load(filename, path=""):
        """loads a surrogate from the file in filename."""
        if path:
            filename = os.path.join(path, filename)
        if not os.path.exists(filename):
            raise DelisMMError("No such file: " + filename)
        with open(filename, "rb") as f:
            surrogate = pickle.load(f)
        if isinstance(surrogate, AbstractKriging) and not surrogate.isCreated:
            surrogate.createSurrogateModel(surrogate.theta)
        surrogate.isCorrectVersion()
        if hasattr(surrogate, "log10SampleX"):
            # probably due to loading pickled surrogates, the bool values changed. Thus setting actual bools
            # print(surrogate.log10SampleX[0] is False)
            surrogate.log10SampleX = [(False if z == False else True) for z in surrogate.log10SampleX]
            # print(surrogate.log10SampleX[0] is False)
        log.info('Surrogate with name "{}" loaded from {}'.format(surrogate.name, filename))
        return surrogate

    def isCorrectVersion(self):
        """Checks the version of a surrogate instance with the actual Surrogate class version

        This method must be implemented in a subclass in order to take effect."""
        return True

    def _getSampleX(self):
        """doc"""
        return BoundsHandler.scaleToBoundsStatic(self.sampleXNormalized, self.lowerBounds, self.upperBounds)

    sampleX = property(fget=_getSampleX)


class ImproveKrigingModel(AbstractSurrogate):
    """
    This is a class which contains methods to improve an existing Kriging Model. Therefore the class AbstractKriging inherits the methods.
    You should not instanciate this class directly.
    """

    def refineKrigingModelNoGridding(
        self,
        targetFunctionInstance,
        maxNrOfNewPoints,
        maxTime=60 * 60 * 24 * 2,
        initOptiPoints=None,
        samplingOptCrit="mse",
        doRemoteCall=False,
        runDir=None,
    ):
        """Refines the kriging model without using adaptive gridding. This might be good for initial
        new samples that should be spread over the design space without checking maxRelError.
        A new theta value is calculated at the end of this method

        :param targetFunctionInstance: instance of a delismm.model.customsystemfunction class (or a derived one),
            that can be evaluated to generate new sample data
        :param maxNrOfNewPoints: number of new sample points
        :param maxTime: time limit [s]
        :param initOptiPoints: number of restarts of local optimization
        :param samplingOptCrit: string that defines the function to maximize: ['mse','det','vfmError','vfmCorrelation'].
        :return: new Kriging model
        """
        if initOptiPoints is None:
            initOptiPoints = 5 * self.p
        log.info("Refine Kriging model without adaptive gridding")
        log.info(
            "samplingOptCrit = "
            + str(samplingOptCrit)
            + ", maxTime = "
            + str(maxTime)
            + ", nrOfNewPoints = "
            + str(maxNrOfNewPoints)
        )
        startTime = time.time()
        lower = np.array([0.0] * self.p)
        upper = np.array([1.0] * self.p)
        krigingModel = copy.copy(self)
        newXs = []
        for _ in range(maxNrOfNewPoints):
            if time.time() - startTime > maxTime:
                log.info("Time Limit (" + str(maxTime) + ") has been reached!")
                break
            newX = krigingModel.newX(lower, upper, None, initOptiPoints, samplingOptCrit)
            newXs.append(newX)
            newY = targetFunctionInstance(BoundsHandler.scaleToBoundsStatic(newX, self.lowerBounds, self.upperBounds))
            if not isinstance(newY, str) and hasattr(newY, "__iter__"):
                newY = newY[0]
            nKrigingModel = krigingModel.n
            sampleXNormalized = np.zeros((self.p, nKrigingModel + 1))
            sampleXNormalized[:, :nKrigingModel] = copy.copy(krigingModel.sampleXNormalized)
            sampleXNormalized[:, -1] = newX
            sampleY = np.zeros((nKrigingModel + 1,))
            sampleY[:nKrigingModel] = copy.copy(krigingModel.sampleY)
            sampleY[-1] = newY
            krigingModel = self.getCopyNewSamples(sampleXNormalized, sampleY)
            oldLogLevel = krigingModel.logLevel
            krigingModel.logLevel = log.DEBUG
            krigingModel.createSurrogateModel()
            krigingModel.logLevel = oldLogLevel
        # recalculate theta
        krigingModel.createSurrogateModel(self.theta, forceOptTheta=True, doRemoteCall=doRemoteCall, runDir=runDir)
        log.info("I found new sample points: " + indent(newXs))
        log.info("Kriging Model refinement finished. Added " + str(krigingModel.n - self.n) + " sample points.")
        return krigingModel

    def refineKrigingModel(
        self,
        targetFunctionInstance,
        maxRelError=0.05,
        maxLoops=float("inf"),
        maxTime=60 * 60 * 24 * 2,
        maxNumberNewGriddingPoints=50,
        initOptiPoints=None,
        samplingOptCrit="mse",
        doRemoteCall=False,
        runDir=None,
    ):
        """Creates a new Kriging model by adaptive gridding.
        :param targetFunctionInstance: instance of a delismm.model.customsystemfunction class (or a derived one),
            that can be evaluated to generate new sample data
        :param maxLoops: maximal number of loops
        :param maxTime: time limit [s]
        :param maxNumberNewGriddingPoints: maximal number of new sample points
        :param maxRelError: target accuracy, evaluation criterion for cross validation
        :param initOptiPoints: number of restarts of local optimization
        :param samplingOptCrit: string that defines the function to maximize: ['mse','det','vfmError','vfmCorrelation'].
        :return: new Kriging model
        """
        if initOptiPoints is None:
            initOptiPoints = 5 * self.p
        log.info(
            "samplingOptCrit = "
            + str(samplingOptCrit)
            + ", maxRelError = "
            + str(maxRelError)
            + ", maxTime = "
            + str(maxTime)
            + ", maxNumberNewGriddingPoints = "
            + str(maxNumberNewGriddingPoints)
        )
        loopCount = 1
        startTime = time.time()
        krigingModel = copy.copy(self)
        while True:
            if loopCount > maxLoops:
                log.info("Maximal number of loops (" + str(maxLoops) + ") has been reached!")
                break
            if krigingModel.n - self.n > maxNumberNewGriddingPoints:
                log.info("Maximal number of new points (" + str(maxNumberNewGriddingPoints) + ") has been reached!")
                break
            if time.time() - startTime > maxTime:
                log.info("Time Limit (" + str(maxTime) + ") has been reached!")
                break
            log.info("Refine Kriging model. Loop " + str(loopCount))

            oldLogLevel = krigingModel.logLevel
            krigingModel.logLevel = log.DEBUG
            newSampleXNormalized = krigingModel._adaptiveGridding(
                maxRelError, self.n + maxNumberNewGriddingPoints - krigingModel.n, initOptiPoints, samplingOptCrit
            )
            krigingModel.logLevel = oldLogLevel

            if newSampleXNormalized is None:
                log.info("No new Samples found with maxRelError (" + str(maxRelError) + "). Refinement finished.")
                break
            newSampleCount = newSampleXNormalized.shape[1] + krigingModel.n
            oldSampleXNormalized = copy.copy(krigingModel.sampleXNormalized)
            ssampleY = copy.copy(krigingModel.sampleY)

            # calculate new sampleY
            newSampleX = BoundsHandler.scaleToBoundsStatic(newSampleXNormalized, self.lowerBounds, self.upperBounds)
            newSampleY = np.array(getY(newSampleX, targetFunctionInstance)).flatten()
            # put samples thogether
            sampleXNormalized = np.zeros((self.p, newSampleCount))
            sampleXNormalized[:, 0 : krigingModel.n] = oldSampleXNormalized
            sampleXNormalized[:, krigingModel.n : newSampleCount] = newSampleXNormalized
            sampleY = np.zeros((newSampleCount,))
            sampleY[0 : krigingModel.n] = ssampleY
            sampleY[krigingModel.n : newSampleCount] = newSampleY
            krigingModel = self.getCopyNewSamples(sampleXNormalized, sampleY)
            # recalculate theta
            krigingModel.createSurrogateModel(self.theta, forceOptTheta=True, doRemoteCall=doRemoteCall, runDir=runDir)
            loopCount += 1
        log.info("Kriging Model refinement finished. Added " + str(krigingModel.n - self.n) + " sample points.")
        return krigingModel

    def _adaptiveGridding(self, maxRelError, maxNumberNewGriddingPoints, initOptiPoints, samplingOptCrit):
        """Splits the design space in equal-sized, hypercuboid cells and evaluates the cells via cross validation.
        Returns new sample points in 'bad' cells.
        :param maxRelError: target relative accuracy (relative to the associated sampleY-value)
        :param maxNumberNewGriddingPoints: maximal number of new points that can be selected
        :param initOptiPoints: number of initial points for local optimization
        :param samplingOptCrit: string that defines the function to maximize: ['mse','det','vfmError','vfmCorrelation'].
        :return: numpy-matrix with new sample points (column by column)

        """
        maxDivisions = 10  # maximal number of interval divisions
        minDivisions = 2  # minimal number of interval divisions

        # create a tuple divisionNumbers in which the number of interval divisions of each koordinate axis is stated
        # create a np.array intervalLen in which the length of the subintervals is stated
        divisionNumbers = []
        intervalLen = []
        for thetaJ in self.theta:
            length = 1.0
            if self.corr == "cubic":
                thetaJ = thetaJ * 10  # cubic correlation only allows theta to be at max = 1
            number = int(length * thetaJ) + 1
            if number < minDivisions:
                number = minDivisions
            if number > maxDivisions:
                number = maxDivisions
            intervalLen.append(length / number)
            divisionNumbers.append(number)
        intervalLen = np.array(intervalLen)
        divisionNumbers = tuple(divisionNumbers)
        # list of all adapted sample points
        newXs = []
        # iterate over all sub-hypercubes defined by the subintervals
        for i in range(np.prod(divisionNumbers)):
            if maxNumberNewGriddingPoints - len(newXs) <= 0:
                break
            # lower and upper bounds of the hypercube
            lower = np.array(np.unravel_index(i, divisionNumbers)) * intervalLen
            upper = np.ones((self.p,)) * intervalLen + lower
            # copy of the sampleXNormalized array as a list; the entries of the list are the sample points as np.arrays
            subset = copy.copy(list(self.sampleXNormalized.T))
            # iterate over the different coordinate axes and over the sample points and test, whether a point lies within the hypercube
            for k in range(self.p):
                pointIndex = 0
                while pointIndex < len(subset):
                    # if the point doesn't lie within the hypercube, remove it from subset
                    if (
                        subset[pointIndex][k] < lower[k]
                        or subset[pointIndex][k] > upper[k]
                        or subset[pointIndex][k] < 1e-15
                        or 1 - subset[pointIndex][k] < 1e-15
                    ):
                        subset.pop(pointIndex)
                    else:
                        pointIndex = pointIndex + 1
            # do a cross validation for subset
            if len(subset) == 0:
                badIndex, badValue = None, 0.0
            else:
                badIndex, badValue = self._crossValidationSubset(subset)[:-1]
            if badValue > np.abs(np.max(self.sampleY) - np.min(self.sampleY)) * maxRelError or badIndex is None:
                newX = self.newX(lower, upper, badIndex, initOptiPoints, samplingOptCrit)
                isNew = True
                for k in range(len(newXs)):
                    if np.linalg.norm(newX - newXs[k]) < 1e-7:
                        isNew = False
                        break
                if isNew:
                    newXs.append(newX)
        if newXs == []:
            log.debug("No new sample points required.")
            return None
        log.info("I found new sample points: " + indent(newXs))
        return np.array(newXs).T

    def getCrossValidationValues(self, doRemoteCall=False, runDir=None):
        """Performs a crossvalidation of this metamodel and returns the cross validation values

        :return: np.ndarray of len self.n with values of crossValidation in the
            order like self.sampleXNormalized
        """
        oldLogLevel = self.logLevel
        self.logLevel = log.DEBUG
        crossValidationDifferences = self._crossValidationSubset(
            self.sampleXNormalized.T, doRemoteCall=doRemoteCall, runDir=runDir
        )[2]
        crossValidationDifferences = np.array(crossValidationDifferences).flatten()
        self.logLevel = oldLogLevel
        return self.sampleY - crossValidationDifferences

    def _crossValidationSubset(self, subset, doParallelization=True, doRemoteCall=False, runDir=None):
        """Returns the maximum of the cross validation of subset's elements.
        It is a measure for the error of the metamodel.

        :param subset: set of points for cross validation, must be a subset of support points sampleXNormalized; type = list
        :return: triple (index of the worst cross-validation value, cross-validation difference at that index, np array with all cross-validation values),
            where index is the index of the maximum cross-validation point in sampleXNormalized
            and cross-validation value is the according value of cross validation.
        """
        if len(subset) == 0:
            return (-1, 10**20, [])
        listOfSupports = list(self.sampleXNormalized.T)
        listOfSupportValues = list(self.sampleY)
        # Erstellen einer Liste mit cross validation values
        args = (listOfSupports, listOfSupportValues)
        if 0:  # local serial calculation or parallel calculation
            indexInSampleX = []
            crossValidationDiffs = []
            for crossX in subset:
                crossValidationDiff, index = self.crossValidation(crossX, *args)
                crossValidationDiffs.append(crossValidationDiff)
                indexInSampleX.append(index)
        else:
            cvTargetFunction = CrossValidationValuesCalculatorKriging(self, args, doRemoteCall, runDir=runDir)
            if not doParallelization:
                cvTargetFunction.doParallelization = []
            log.info('Perform crossvalidation for kriging model "{}"'.format(self.name))
            result = getY(np.array(subset).T, cvTargetFunction, False)
            crossValidationDiffs, indexInSampleX = list(zip(*result))
        maxi = np.max(np.abs(crossValidationDiffs))
        maxiIndexInSubset = np.abs(crossValidationDiffs).argmax()
        maxiIndexInSampleX = indexInSampleX[maxiIndexInSubset]
        absRelError = maxi / np.abs(np.max(self.sampleY) - np.min(self.sampleY))
        log.info(
            "Max abs cross validation abs and scaled error : "
            + str(maxi)
            + ", "
            + str(absRelError)
            + " at "
            + str(subset[maxiIndexInSubset])
        )

        return (maxiIndexInSampleX, maxi, crossValidationDiffs)

    def crossValidation(self, crossX, listOfSupports, listOfSupportValues):
        """Calculates the cross validation diff of one sample"""
        supports = copy.copy(listOfSupports)
        supportValues = copy.copy(listOfSupportValues)
        # Entferne eine Stuetzstelle aus der Liste
        index = 0
        # find correct index for crossX
        while index < len(supports) and not np.linalg.norm(crossX - supports[index]) < 1.0e-15:
            index = index + 1
        if index == len(supports):
            raise ValueError("sample of subset not found in self.sampleXNormalized")
        sampleY = supportValues[index]
        supports.pop(index)
        supportValues.pop(index)
        supports = np.array(supports).T
        # Metamodell ueber die restlichen Stuetzstellen
        crossKriging = self.getCopyNewSamples(supports, np.array(supportValues))
        crossKriging.createSurrogateModel(theta=self.theta)
        # fuege Differenz von original Metamodell-Wert und neuem Metamodell-Wert zu Liste hinzu
        crossY = crossKriging.callNormalized(crossX.T)
        if self.log10SampleY:
            # calculate in log-space
            crossY = np.log10(crossY)
        crossValidationDiff = sampleY - crossY
        return crossValidationDiff, index

    def newX(self, lower, upper, badIndex, initOptiPoints, samplingOptCrit):
        """Returns a np.array with the coordinates of a new point within the subcube [lower,upper].
        The new point is choosen via the method given in samplingOptCrit (by default: samplingOptCrit = 'mse')
        :param lower: array with lower bounds of the hypercube
        :param upper: array with upper bounds of the hypercube
        :param badIndex: index of the worst point of the subset
        :param initOptiPoints: number of start points for local optimization
        :param samplingOptCrit: string that defines the function to maximize: ['mse','det','vfmError','vfmCorrelation'].
        :return: the new point
        """
        # ===========================================================================================
        # create start values for local opt
        # ===========================================================================================
        initOptiPoints = 4
        bounds = []
        for i in range(self.p):
            bounds.append((lower[i], upper[i]))
        x0s = []
        if badIndex is None:  # no samples in the subset. Thus a sample should be created here
            x0s.append(lower + (upper - lower) / 2)
        else:
            badPlusEps = (
                1.0e-7 * np.ones(self.sampleXNormalized[:, badIndex].shape) + self.sampleXNormalized[:, badIndex]
            )
            badMinusEps = (
                -1.0e-7 * np.ones(self.sampleXNormalized[:, badIndex].shape) + self.sampleXNormalized[:, badIndex]
            )
            if not np.any(badPlusEps < lower) or np.any(badPlusEps > upper):
                # badPlusEps is within bounds
                x0s.append(list(badPlusEps))
            if not np.any(badMinusEps < lower) or np.any(badMinusEps > upper):
                # badMinusEps is within bounds
                x0s.append(list(badMinusEps))
        while len(x0s) <= initOptiPoints:
            newx0s = []
            for i in range(self.p):
                newx0s.append(random.uniform(lower[i], upper[i]))
            isIn = False
            for i in range(len(x0s)):
                if np.linalg.norm(np.array(x0s[i]) - np.array(newx0s), 2) <= 1.0e-15:
                    isIn = True
                    break
            if not isIn:
                x0s.append(newx0s)

        # ===========================================================================================
        # set opt function
        # ===========================================================================================
        f = self.getSamplingOptFunction(samplingOptCrit)
        fMin = lambda x: -1 * f(x)
        #         maxF0 = np.max([f(np.array(x).T) for x in x0s])
        #         f = self.getSamplingOptFunction(samplingOptCrit)
        #         fScaled = lambda x: -1 * f(x) / maxF0

        # =======================================================================
        # parform optimization
        # =======================================================================
        bounds = list(zip(lower, upper))
        #         optimum = self._getGlobalOptimum(f, bounds)
        optimum = self._doGlobalOpt(fMin, bounds, doRemoteCall=False)

        log.debug(
            "Opt results (TargetValue, thetas):  \n"
            + indent([[self.optThetaGlobalLocalType] + [optimum.fun] + list(optimum.x)])
        )
        return optimum.x

    def getSamplingOptFunction(self, samplingOptCrit):
        """Returns the function to optimize the location of a new sample point.

        :param samplingOptCrit: string that defines the function to maximize: ['mse','det','vfmError'].
        :return: function pointer to target function
        """
        if samplingOptCrit == "mse":
            return self.getMSEofPredictor
        elif samplingOptCrit == "det":
            return self._optimizeNewR
        elif samplingOptCrit == "vfmError":
            if not isinstance(self, HierarchicalKriging):
                raise DelisMMError("Could not use the relative hierarchical kriging error")
            # MSE * abs(relative error - 1)
            return self._optimizeVfmError
        elif samplingOptCrit == "vfmCorrelation":
            if not isinstance(self, HierarchicalKriging):
                raise DelisMMError("Could not use the relative hierarchical kriging error")
            # MSE * abs(Kriging_correlation)
            return self._optimizeMseAndCorrelation
        elif hasattr(samplingOptCrit, "__call__"):
            # samplingOptCrit is a kriging model or an other targetFunction
            # using the relative error function of self and the given function
            self.otherTargetFunc = samplingOptCrit
            return self._optimizeRelErrorWithOtherTargetFunc
        else:
            raise DelisMMError(
                "No proper criterion as function to maximize for new sample given. These are the allowed ones: ['mse','det','vfmError']"
            )

    def _optimizeRelErrorWithOtherTargetFunc(self, x):
        """doc"""
        valueSelf, valueOther = self(x), self.otherTargetFunc(x)
        return 1 - np.min([valueSelf, valueOther]) / np.max([valueSelf, valueOther])

    def _optimizeVfmError(self, x):
        """Only works for hierarchical models"""
        minByMax = np.min([self(x), self.lfKriging(x)]) / np.max([self(x), self.lfKriging(x)])
        return self.getMSEofPredictor(x) * (1 - minByMax)

    def _optimizeMseAndCorrelation(self, x):
        """Only works for hierarchical models"""
        corrVec = self.getCorrelationVector(x)
        correlationValue = (corrVec.T @ self.v)[0, 0]
        return self.getMSEofPredictor(x) * np.abs(correlationValue)

    def _optimizeNewR(self, newX):
        """Function for optimization process. This function needs to be minimized for optimal new sample point
        :param newX: point within subcube
        :return: ln(det(newR))
        """
        newR = np.zeros((self.n + 1, self.n + 1))
        newR[0 : self.n, 0 : self.n] = self._R
        for i in range(self.n):
            newR[self.n, i] = self._correlationFunction(self.sampleXNormalized[:, i], newX, self.theta)
            newR[i, self.n] = newR[self.n, i]
            newR[i, i] = 1.0e-11 + newR[i, i]
        newR[self.n, self.n] = 1.0e-11 + 1.0
        try:
            cholR = np.linalg.cholesky(newR)
        except np.linalg.LinAlgError:
            log.info("Matrix ist nicht positiv definit!")
            return -(10**20)
        lnDet = 0.0
        for i in range(self.n + 1):
            lnDet = lnDet + 2 * np.log(cholR[i, i])
        return lnDet


class AbstractKriging(ImproveKrigingModel):
    """init"""

    version = delismmVersion

    def __init__(
        self, sampleX, sampleY, lowerBounds, upperBounds, corr, regress="const", parameterNames=None, resultNames=None
    ):
        """Kriging class for common methods of Kriging and hierarchical Kriging"""
        AbstractSurrogate.__init__(self, sampleX, sampleY, lowerBounds, upperBounds, parameterNames, resultNames)

        self.version = self.version
        """set class attribute "version" as instance attribute for checking when the surrogate is loaded"""
        # =======================================================================
        # Kriging important public attributes
        # =======================================================================
        corrModels = ["gauss", "exp", "cubic"]
        if corr not in corrModels:
            raise DelisMMError(f"Wrong correlation model name given. These are applicable models: {corrModels}")
        self.corr = corr
        """ corr is a string which declares the used correlation model. corr can be 'gauss', for gaussian correlation,
            'exp', for exponential correlation or 'cubic' for cubic correlation. """

        regressModels = ["const", "linear"]
        if regress not in regressModels:
            raise DelisMMError(f"Wrong regression model name given. These are applicable models: {regressModels}")
        self.regress = regress
        """Regression model - either constant or linear regression"""

        self.n = self.sampleXNormalized.shape[1]  # n - Number of sample points
        """ n is the number of sample points """
        self.p = self.sampleXNormalized.shape[0]  # p - Number of design variables
        """ p is the dimension of the design space/ the number of model parameters """
        self.theta = None
        """ theta is the correlation parameter and defines the regression width of the regression function.
        It can be set by the keyword argument 'theta'. If it is not set by the user, theta is determined by
        an maximum likelihood optimization. It is a 1D array: np.array([theta_1,theta_2 .. theta_p])"""

        self.regularizationParameter = 1e-11
        """"regularization to the correlation matrix"""
        self.doRegularizationParameterOpt = True
        """Switch that performs the optimization of the regularization parameter"""

        self.name = "kriging"
        if self.resultNames:
            self.name += "_" + self.resultNames[0]

        # =======================================================================
        # theta optimization attributes
        # =======================================================================
        self.optThetaGlobalLocalType = "global"
        """Type of optimization run. These string values are valid: [global, local].
        Global or pure local optimization can be performed. After each global optimization run,
        the scipy optimizer performs a local optimization. The global optimizations are
        repeated self.optThetaGlobalAttempts times.
        """
        self.optThetaGlobalAttempts = 6
        """Integer, describing the attempts to perform a global local optimization"""
        self.optThetaMaxIter = 10**3
        """Maximal Iterations of one population within the theta optimization"""
        self.optThetaPrintout = False
        """print text output every <optThetaPrintout> iteration"""

        # =======================================================================
        # result values of a created model
        # =======================================================================
        self.correlationMatrixAlgo = "fast"
        """[fast, memory] String that determines the correlation matrix method used.
        _getCorrelationMatrixMemory is slow but requires less memory, _getCorrelationMatrixFast is fast but requires much memory"""
        self._R = None
        self._modifiedCorrMatrix = None
        """block matrix, eq 3.20
        [ R    F
          F.T  0 ]"""
        self.condition = None
        """ Condition number (2-norm) of modified correlation matrix (left hand side of system which must be solved to evaluate metamodell at a given point) """
        self.beta0 = None
        """ Regression parameters """
        self.v = None
        self._F = None
        """regressionFunctionValues F(n,p+1) = [f(x^1), ..., f(x^n)]"""

    def createSurrogateModel(self, theta=None, forceOptTheta=False, doRemoteCall=False, runDir=None):
        """Creates the kriging model. Here all result variables are set as private class attributes."""

        log.log(self.logLevel, "Start constructing a surrogate of type " + str(self.__class__.__name__))
        log.debug('Correlation model "%s"' % self.corr)
        if hasattr(self, "regress"):
            log.debug('Regression model "%s"' % self.regress)
        self._F = self._getRegressionFunctionValues()
        # Theta optimization
        if (theta is None and self.theta is None) or forceOptTheta:
            log.debug("Start theta optimization.")
            if not forceOptTheta and (theta is None and self.theta is not None):
                theta = self.theta
            self.theta, self.regularizationParameter = self._optimizeHyperparams(theta, doRemoteCall, runDir)
            log.log(self.logLevel, "Found theta. Optimization was successful.")
        else:
            if theta is not None:
                self.theta = np.abs(theta)
        log.debug("theta = " + str(self.theta))

        self._R = self._getCorrelationMatrix(self.theta, self.regularizationParameter)
        self._modifiedCorrMatrix = self._getModifiedCorrMatrix()
        """necessary for getMSEofPredictor"""
        self.condition = np.linalg.cond(self._modifiedCorrMatrix)
        """ Condition number (2-norm) of modified correlation matrix (left hand side of system which must be solved to evaluate metamodell at a given point) """
        log.debug("Condition number: " + str(self.condition))

        self.beta0 = self.getBeta(self._F, self._R, self.sampleY, symPos=False)
        """ Regression parameters """
        self.v = self.getV(self._F, self._R, self.sampleY, self.beta0)
        log.log(self.logLevel, "End constructing a surrogate of type " + str(self.__class__.__name__))

    def regressionFunction(self, xNormalized):
        """Evaluates the regression part of the model at a specific point of interest
        f(x)*beta in annas work"""
        regressVec = self._regressionVector(xNormalized)
        return regressVec @ self.beta0

    def _regressionVector(self, xNormalized):
        """Vector for evaluation of the regression model.

        For Kriging objects, the regression function can be chosen by setting the model parameter 'regress'.
        For HierarchicalKriging objects, the regression function is the Kriging model of lf Data.
        :param x: point to be evaluated
        :return: regression function value
        """
        if self.regress == "const":
            return [1]
        elif self.regress == "linear":
            regressionValues = np.ones((self.p + 1,))
            regressionValues[1:] = xNormalized
            return regressionValues
        else:
            raise DelisMMError("Only these values are applicable for parameter regress: [linear, const].")

    def _getRegressionFunctionValues(self):
        """
        Returns a matrix with the regression function values of the sample points. F = (f(x1),...,f(xn)).T
        :return: matrix with regression function values of sample points
        p. 14, top in annas work F=...
        """

        F = []
        for i in range(self.n):
            F.append(self._regressionVector(self.sampleXNormalized[:, i]))
        return np.array(F)

    def _getCorrelationMatrix(self, theta, regularizationParameter):
        """Returns the correlation matrix of the sample points

        It uses the numpy arrays to calculate each entry of R with one call. Thus it is fast but
        requires much memory. If you get a memory error, you should switch to python64 or use
        self._getCorrelationMatrixMemory which is very slow.
        :return: correlation matrix R
        """
        # ===========================================================================================
        # map sample x onto an array in axis=0 and axis=1
        # Example:
        # p=2
        # sampleX = np.array([[0.,1.,3.],[1.,2.,4.]])
        #
        # sk, sk.shape
        # [ 0.  1.] | [ 1.  2.] | [ 3.  4.]
        # [ 0.  1.] | [ 1.  2.] | [ 3.  4.]
        # [ 0.  1.] | [ 1.  2.] | [ 3.  4.]
        # (3, 3, 2)
        #
        # si, si.shape
        # [ 0.  1.] | [ 0.  1.] | [ 0.  1.]
        # [ 1.  2.] | [ 1.  2.] | [ 1.  2.]
        # [ 3.  4.] | [ 3.  4.] | [ 3.  4.]
        # (3, 3, 2)
        # ===========================================================================================
        sk = np.ones((self.n, self.n, self.p)) * self.sampleXNormalized.T
        sampleDiffs = sk.transpose((1, 0, 2)) - sk
        del sk  # remove sk to save memory

        R = self._correlationFunction(sampleDiffs, theta)
        R = R + np.identity(self.n) * regularizationParameter

        return R

    def correlationFunction(self, x, z):  # spatial correlation of two points in design space
        """Returns the correlation between x and z

        :param x: point of interest (dimension p)
        :param z: other point of interest (dimension p)
        :return: correlation value
        """
        x = np.ones((1, 1, self.p)) * x
        z = np.ones((1, 1, self.p)) * z

        return self._correlationFunction(x - z, self.theta)[0]

    def correlationFunctionNSamples(self, x, z):
        """Returns the correlation between x and z where x and z contain several samples

        :param x: points of interest (dimension (m,p))
        :param z: other points of interest (dimension (m,p))
        :return: correlation vector
        """
        x = np.array(x)
        x, z = np.ones((1, x.shape[0], self.p)) * x, np.ones((1, x.shape[0], self.p)) * z

        return self._correlationFunction(x - z, self.theta)

    def _correlationFunction(self, sampleDifferences, theta):
        """Returns the spatial correlation of each point in self.sampleXNormalized.

        You can choose the spatial correlation model by setting the model parameter 'corr'.
        :param sampleDifferences: (n,n,p)-array which is the difference as sampleXNormalized[k]-sampleXNormalized[i] where k,i= 1 .. n
        :param theta: spatial correlation parameter
        :return: spatial correlation matrix
        """
        if self.corr == "gauss":
            return np.exp(-np.sum(theta * (np.abs(sampleDifferences)) ** 2, 2))
        elif self.corr == "exp":
            return np.exp(-np.sum(theta * np.abs(sampleDifferences), 2))
        elif self.corr == "cubic":
            # using inline array replacements for memory efficiency
            sampleDifferences = theta * np.abs(sampleDifferences, sampleDifferences)
            np.fmin(sampleDifferences, np.ones_like(sampleDifferences), sampleDifferences)  # fmin used to save memory
            return np.prod(1 - 3 * sampleDifferences**2 + 2 * sampleDifferences**3, 2)
        else:
            raise DelisMMError('Surrogate parameter "corr" must be one of [gauss, exp, cubic]')

    def _getCorrelationMatrixMemory(self, theta, regularizationParameter):
        """Returns the correlation matrix of the sample points.

        It uses a python-style loop to calculate
        each entry in R. Thus it is quite slow but memory efficient.
        :return: correlation matrix R
        """
        r = np.identity(self.n) * (1 + regularizationParameter)
        for i in range(self.n):
            for k in range(i + 1, self.n):
                res = self._correlationFunctionMemory(self.sampleXNormalized[:, i], self.sampleXNormalized[:, k], theta)
                r[i, k] = res
                r[k, i] = res
        return r

    def _correlationFunctionMemory(self, x, z, theta):  # spatial correlation of two points in design space
        """Returns the spatial correlation of two points.

        You can choose the spatial correlation model by setting the model parameter 'corr'.
        :param x: first point
        :param z: second point
        :param theta: spatial correlation parameter
        :return: spatial correlation of x and z
        """
        if self.corr == "gauss":
            summand = theta * (np.abs(x - z)) ** 2
            r = np.exp(-np.sum(summand))
        elif self.corr == "exp":
            summand = theta * (np.abs(x - z))
            r = np.exp(-np.sum(summand))
        elif self.corr == "cubic":
            r = 1
            if self.p == 1:
                xij = np.amin([[1], theta * np.abs(x - z)[0]])
                xij = np.float64(xij)
                r = 1 - 3 * xij**2 + 2 * xij**3
            else:
                for j in range(self.p):
                    # the following if-clause had is needed because with p=2 design parameters there may be x-values that are floats and no array
                    #                    if type(x) is not np.ndarray:
                    #                        log.info('wrong x vector: '+str(x)+str(type(x))+'x vector set manually to length of self.p')
                    #                        x = np.zeros(self.p, np.ndarray)
                    #                    elif type(z) is not np.ndarray:log.info('wrong z vector: '+str(z)+str(type(z)))
                    #                    elif type(theta) is not np.ndarray:log.info('wrong theta vector: '+str(theta)+str(type(theta)))
                    xij = np.amin([1, theta[j] * np.abs(x[j] - z[j])])
                    rj = 1 - 3 * xij**2 + 2 * xij**3
                    r = r * rj
        else:
            raise DelisMMError("corr muss gauss, exp oder cubic sein!")
        return r

    def getCorrelationVectorMemory(self, x):
        """Returns the correlation vector of a point x and the sample points

        :param x: point of interest
        :return: correlation vector
        """
        vector = np.zeros((self.n, 1))
        for i in range(self.n):
            vector[i, 0] = self._correlationFunctionMemory(x, self.sampleXNormalized[:, i], self.theta)
        return vector

    def getCorrelationVector(self, x):
        """Returns the correlation vector of a point x and the sample points, eq. 3.15, see r(x)

        :param x: point of interest
        :return: correlation vector
        """
        si = np.ones((1, self.n, self.p)) * self.sampleXNormalized.T
        r = self._correlationFunction(si - x, self.theta)
        return r.T

    def _getModifiedCorrMatrix(self):
        """Returns the block matrix

        [ R    F
          F.T  0 ]
        where R is the correlation matrix of the sample points and F is the regression function value matrix.
        This matrix is used to evaluate the surrogate model.
        :return: matrix [[R,F];[F.T,0]]"""
        regressionValues = self._F
        if self.regress == "const":
            dim = self.n + 1
            retArray = np.zeros((dim, dim))
            retArray[self.n : dim, 0 : self.n] = regressionValues.T
            retArray[0 : self.n, self.n : dim] = regressionValues
            for i in range(self.n):
                retArray[self.n, i] = 1
                retArray[i, self.n] = 1
        elif self.regress == "linear":
            dim = self.n + self.p + 1
            retArray = np.zeros((dim, dim))
            retArray[self.n : dim, 0 : self.n] = regressionValues.T
            retArray[0 : self.n, self.n : dim] = regressionValues
        retArray[0 : self.n, 0 : self.n] = self._R
        return retArray

    def negLnLikelihoodExpOptParamWrapper(self, optParameters):
        """wrapper around the negLnLikelihood optimization target function.

        For the optimization theta is not used directly but :math:`thetaExp = log_{10}(theta)` is used instead.
        Hence, this method will wrap the thetaExp from the exponential form to the non exponential form.
        """
        optParameters = np.power(10, optParameters)
        return self.negLnLikelihood(optParameters)

    def negLnLikelihood(
        self, optParameters
    ):  # dient zur Optimierung bezueglich theta, zunaechst simplified covariance data fitment 2.5.3
        """
        Implementation of the condensed log-likelihood function, used to optimize the correlation parameter theta.

        see eq. 3.33

        :param optParameters: list of all thetas and the regularizationParameter
        :return: condensed log-likelihood function value
        """
        if self.doRegularizationParameterOpt:
            theta = optParameters[:-1]
            regularizationParameter = optParameters[-1]
        else:
            theta = optParameters
            regularizationParameter = self.regularizationParameter
        R = self._getCorrelationMatrix(theta, regularizationParameter)

        try:
            cholR = np.linalg.cholesky(R)
        except (np.linalg.linalg.LinAlgError, linalg.LinAlgWarning):
            log.debug("Matrix ist nicht positiv definit! theta = " + str(theta))
            return np.inf  # 10**20
        lnDet = np.sum(2 * np.log(cholR.diagonal()))
        try:
            solveRegress = linalg.solve(R, self._F, assume_a="pos")
        except (np.linalg.linalg.LinAlgError, linalg.LinAlgWarning):
            log.warning(
                "Regression function could not be calculated due to a singular matrix. "
                "This parameter set will be igonred. Please check your in- and output for "
                "theta = " + str(theta)
            )
            return np.inf

        solveYs = linalg.solve(R, self.sampleY, assume_a="pos")
        beta = np.linalg.solve(self._F.T @ solveRegress, self._F.T @ solveYs)
        sigmaSq = self.getSigmaSqared(R, beta, solveYs)
        result = self.n * np.log(sigmaSq) + lnDet
        return result

    @staticmethod
    def getV(F, R, Y, beta):
        """Eq 3.23 from Sauerbrei

        :param F: Regression function values eq.
        :param R: Correlation matrix
        :param Y: function values at samples
        :param symPos: flag if correlation matrix is assumed to be positive definite
        """
        v = linalg.solve(R, Y - F @ beta)
        return v

    @staticmethod
    def getBeta(F, R, Y, symPos=True):
        """Eq 3.32 from Sauerbrei

        :param F: Regression function values eq.
        :param R: Correlation matrix
        :param Y: function values at samples
        :param symPos: flag if correlation matrix is assumed to be positive definite
        """

        try:
            solveRegress = linalg.solve(R, F, assume_a="pos" if symPos else "gen")
        except np.linalg.linalg.LinAlgError:
            log.warning(
                "Regression function could not be calculated due to a singular matrix. This parameter set will be igonred."
            )
            return np.inf

        solveYs = linalg.solve(R, Y, assume_a="pos" if symPos else "gen")
        beta = np.linalg.solve(F.T @ solveRegress, F.T @ solveYs)
        return beta

    def _optimizeHyperparams(self, theta=None, doRemoteCall=False, runDir=None):
        """Performs the optimization of theta and the regularization Parameter(often called lambda, in Annas thesis it is epsilon)

        The correlation width theta is chosen for each parameter according to the number of samples, the distribution of the
        samples in the design space and the importance of the respective parameters. There is a optimization
        procedure in order to calculate theta using the target function self.negLnLikelihood.

        There are three variants of optimization runs according to parameter self.optThetaGlobalLocalType:
        - global
        - local

        Pure global or pure local optimization can be performed if the calculations take very long.
        Additionally a combined optimization can be done. In combined mode the best value of the global optimizer
        after 5 iterations is used as starting point for the local optimizer. This is repeated
        "self.optThetaGlobalAttempts"-times.
        :param theta: theta may be given as start value. If not [.2]*self.p is starting point

        :return: tuple, (optimized thetas, regularizationParameter). (Attention: it is not thetaExp!)
        """
        f = self.negLnLikelihoodExpOptParamWrapper
        bounds = self._getThetaOptBounds()
        if self.optThetaGlobalLocalType == "global":
            optResult = self._doGlobalOpt(f, bounds, doRemoteCall, runDir)
        elif self.optThetaGlobalLocalType == "local":
            optResult = self._getLocalOptimum(f, theta, bounds)
        else:
            raise DelisMMError(
                'Given value in self.optThetaGlobalLocalType is incorrect. Got "'
                + str(self.optThetaGlobalLocalType)
                + '" but just one of these values is valid: [global, local]'
            )
        log.debug(
            "Opt results (TargetValue, thetaExp):  \n"
            + indent([[self.optThetaGlobalLocalType] + [optResult.fun] + list(optResult.x)])
        )
        log.debug(
            "Opt results (TargetValue, theta):  \n"
            + indent([[self.optThetaGlobalLocalType] + [optResult.fun] + np.power(10, optResult.x).tolist()])
        )
        optResult = np.power(10, optResult.x)
        if self.doRegularizationParameterOpt:
            regularizationParameter = optResult[-1]
            theta = optResult[:-1]
        else:
            regularizationParameter = self.regularizationParameter
            theta = optResult
        return theta, regularizationParameter

    def _doGlobalOpt(self, f, bounds, doRemoteCall=False, runDir=None):
        """doc"""
        optResultHeader = (
            ["f"] + self.parameterNames + (["regularization"] if self.doRegularizationParameterOpt else [])
        )
        if self.optThetaGlobalAttempts == 1 and not doRemoteCall:
            return self._getGlobalOptimum(f, bounds)
        else:
            args = (f, bounds)
            # do parallel run
            optThetaGlobalAttempts = self.optThetaGlobalAttempts
            self.optThetaGlobalAttempts = 1
            thetaOptimizer = ThetaOptimizerKriging(self, args, doRemoteCall, runDir)
            optResults = getY([[0] * optThetaGlobalAttempts], thetaOptimizer, False)
            optValues = [result.fun for result in optResults]
            minResultIndex = np.argmin(optValues)
            optResultArray = [[optResult.fun] + list(optResult.x) for optResult in optResults]
            log.debug("multiple thetaExp opt results:\n" + indent([optResultHeader] + optResultArray))
            nonExpOptResults = np.array(optResultArray)
            nonExpOptResults[:, 1:] = np.power(10, nonExpOptResults[:, 1:])
            log.debug("multiple theta opt results:\n" + indent([optResultHeader] + nonExpOptResults.tolist()))
            self.optThetaGlobalAttempts = optThetaGlobalAttempts
            return optResults[minResultIndex]

    def _getGlobalOptimum(self, f, bounds, maxIter=None):
        """calculates the optimum of f. It performs a global and a successive local search."""
        if maxIter is None:
            maxIter = self.optThetaMaxIter
        log.info("Calculate global opt")
        return differential_evolution(f, bounds, maxiter=maxIter, disp=self.optThetaPrintout)

    def _getLocalOptimum(self, f, theta, bounds):
        """doc"""
        if theta is None:
            theta = 0.2
            thetaExp = np.log10(theta)
            startValue = [thetaExp] * self.p + (
                [self.regularizationParameter] if self.doRegularizationParameterOpt else []
            )
        else:
            thetaExp = np.log10(theta).tolist()
            startValue = thetaExp + [self.regularizationParameter]
        options = {"maxiter": 10**3, "disp": self.optThetaPrintout}
        return minimize(f, startValue, method="L-BFGS-B", bounds=bounds, options=options)

    def _getThetaOptBounds(self):
        """bounds of the correlation model depend on the type of correlation model"""
        lb = self.p * [-3.0] + ([-15.0] if self.doRegularizationParameterOpt else [])
        if self.corr == "cubic":
            ub = self.p * [0.0] + ([-1.0] if self.doRegularizationParameterOpt else [])
        else:
            ub = self.p * [2.0] + ([-1.0] if self.doRegularizationParameterOpt else [])
        return list(zip(lb, ub))

    def getParametersNormalized(self, pointOfInterest):
        if np.any(self.log10SampleX):
            pointOfInterest[self.log10SampleX] = np.log10(pointOfInterest)

        pointOfInterestNormalized = BoundsHandler.scaleTo01Static(
            np.array(pointOfInterest), self.lowerBounds, self.upperBounds
        )
        return pointOfInterestNormalized

    def __call__(self, pointOfInterest):
        """Returns the function value at pointOfInterest.

        :param pointOfInterest: vector of length self.p within real bounds"""
        return self.callNormalized(self.getParametersNormalized(pointOfInterest))

    def callNormalized(self, pointOfInterestNormalized):
        """same as __call__ but uses normalized input samples"""
        self.checkModelCreation()
        corrVec = self.getCorrelationVector(pointOfInterestNormalized)
        regressValue = self.regressionFunction(pointOfInterestNormalized)
        result = regressValue + corrVec.T @ self.v
        if self.log10SampleY:
            result = np.power(10, result)
        return result

    def getSigmaSqared(self, R=None, beta=None, solveYs=None):
        """Calculates sigmasquared from eq 3.30"""
        if R is None:
            R = self._R
        if beta is None:
            beta = self.beta0
        if solveYs is None:
            solveYs = linalg.solve(R, self.sampleY, assume_a="pos")

        solveRegressValues = linalg.solve(R, self._F, assume_a="pos")
        vector = self.sampleY - self._F @ beta
        sigmaSq = (vector.transpose() @ (solveYs - solveRegressValues @ beta)) / self.n
        return sigmaSq

    def getMSEofPredictor(self, pointOfInterestNormalized):
        """Returns the predicted MSE of the Kriging model

        :param pointOfInterestNormalized: point to be evaluated
        :return: predicted MSE at pointOfInterestNormalized"""
        sigmaSq = self.getSigmaSqared()
        solveRegressValues = np.linalg.solve(self._R, self._F)
        corrVec = self.getCorrelationVector(pointOfInterestNormalized)
        solveCorrVec = np.linalg.solve(self._R, corrVec)
        regresssionVector = self._regressionVector(pointOfInterestNormalized)
        vector = corrVec.T @ solveRegressValues - regresssionVector
        mse = sigmaSq * (
            1.0 - corrVec.T @ solveCorrVec + vector * np.linalg.solve(self._F.T @ solveRegressValues, vector.T)
        )
        return mse[0, 0]

    def getExpectedImprovement(self, pointOfInterestNormalized):
        """Calculates the expected improvement function

        Ref: see Forrester et al. [FSK08, Kap. 3] or Diss Freund eq. 3.113

        :param pointOfInterestNormalized: point to be evaluated
        :return: predicted EIF at pointOfInterestNormalized
        """
        s = np.sqrt(self.getMSEofPredictor(pointOfInterestNormalized))
        yMin = np.min(self.sampleY)
        yHat = self.callNormalized(pointOfInterestNormalized)
        yDiff = (yMin - yHat)[0]
        a = yDiff / s

        left = 0.5 * (yDiff) * (1 + special.erf(a / np.sqrt(2)))
        right = s / np.sqrt(2 * np.pi) * np.exp(-0.5 * a**2)

        return left + right

    def checkModelCreation(self):
        """Raises an error, if the model is not created. Returns otherwise"""
        if not self.isCreated:
            raise DelisMMError(
                "The kriging model is not created! Please run createSurrogateModel() prior to this call."
            )

    def getCopyNewSamples(self, sampleXNormalized, sampleY):
        """Returns a copy of self but with adjusted samples. Thus n and p are adjusted as well"""
        kriging = copy.copy(self)
        kriging.sampleXNormalized = sampleXNormalized
        kriging.sampleY = np.array(sampleY)
        kriging.n = sampleXNormalized.shape[1]  # n - Number of sample points
        kriging.p = sampleXNormalized.shape[0]  # p - Number of design variables
        return kriging

    def getKrigingDocumentationDict(self):
        """Returns a OrderedDict with"""
        attributesToDocument = [
            "regularizationParameter",
            "optThetaGlobalLocalType",
            "optThetaGlobalAttempts",
            "optThetaMaxIter",
            "optThetaPrintout",
            "correlationMatrixAlgo",
            "log10SampleX",
            "log10SampleY",
        ]
        docDict = OrderedDict(
            [
                ("kriging_type", self.__class__.__name__),
                ("model_name", self.name),
                ("number_of_samples", self.n),
                ("number_of_parameters", self.p),
                ("condition", self.condition),
                ("correlation_function", self.corr),
                ("regression_function", self.regress),
            ]
            + [(attributeName + "", getattr(self, attributeName)) for attributeName in attributesToDocument]
        )

        if isinstance(self, HierarchicalKriging):
            lowFiModelName = (
                self.lfKriging.name if hasattr(self.lfKriging, "name") else self.lfKriging.__class__.__name__
            )
            docDict.update({"low fi model", lowFiModelName})

        listsToAdd = ["parameterNames", "lowerBounds", "upperBounds", "theta"]
        docDict.update([(listIt, list(getattr(self, listIt))) for listIt in listsToAdd])
        return SurrogateInfo(**docDict)

    def getKrigingDocumentation(self):
        """doc"""
        docDict = self.getKrigingDocumentationDict().model_dump()
        parameterNames = docDict.pop("parameterNames")
        lowerBounds = docDict.pop("lowerBounds")
        upperBounds = docDict.pop("upperBounds")
        theta = docDict.pop("theta")
        keys = [key + ":" for key in docDict.keys()]
        documentation = list(zip(keys, docDict.values()))

        theta = [None] * self.p if theta is None else theta
        boundsArray = [["parameterNames", "lowerBounds", "upperBounds", "thetas"]] + list(
            zip(parameterNames, lowerBounds, upperBounds, theta)
        )

        allSamples = []
        sampleY = np.power(10, self.sampleY) if self.log10SampleY else self.sampleY
        for inputSample, outputSample in zip(self.sampleX.T, sampleY):
            if hasattr(outputSample, "__iter__"):
                allSamples.append(list(inputSample) + list(outputSample))
            else:
                allSamples.append(list(inputSample) + list([outputSample]))

        delim = " "
        return (
            indent(documentation, delim=delim)
            + "\n\nBounds:\n"
            + indent(boundsArray, delim=delim)
            + "\n\nSamples:\n"
            + indent([self.parameterNames + self.resultNames] + allSamples, delim=delim)
        )

    def isCorrectVersion(self):
        """doc"""
        if isinstance(self.version, float) and abs(self.version - 1.1) < 1e-8:
            log.info("Read kriging model of old version. Transform kriging model v1.1 to v1.2")
            self.regularizationParameter = 1e-11  # in v1.1 the regularizationParameter was a constant set to 1e-11
            self.version = "1.2"
        if self.version == "1.2":
            log.info("Read kriging model of old version. Transform kriging model v1.2 to v1.3")
            self.doRegularizationParameterOpt = True
            self.version = "1.3"
        if self.version == "1.3":
            log.info("Read kriging model of old version. Transform kriging model v1.3 to v1.4")
            self.version = "1.4"  # only the inputs and outputs changed
        if self.version == "1.4":
            log.info("Read kriging model of old version. Transform kriging model v1.4 to v1.5")
            oldMatrixAttributes = ["_F", "_R", "_modifiedCorrMatrix", "beta0"]
            for att in oldMatrixAttributes:
                setattr(self, att, np.array(getattr(self, att)))
            self.beta0 = self.getBeta(self._F, self._R, self.sampleY)
            self.v = self.getV(self._F, self._R, self.sampleY, self.beta0)
            self._ys = None  # not used anymore
            self.version = "1.5.0"  # only the inputs and outputs changed
        if self.version == "1.5.0":
            log.info("Read kriging model of old version. Transform kriging model v1.5.0 to v1.6.0")
            self.log10SampleY = False
            self.log10SampleX = np.array([False] * len(self.parameterNames))
            self.version = "1.6.0"

        if self.version.rsplit(".", 1)[0] != self.__class__.version.rsplit(".", 1)[0]:
            log.error(
                "The version of the surrogates read does not correspond to the actual surrogate implementation. "
                + "Actual program version, loaded surrogate version: "
                + str(self.__class__.version)
                + ", "
                + str(self.version)
            )
            return False
        return True

    def save(self, filename, path=""):
        """saves the surrogate to the file in filename."""
        # remove large arrays. They can be recreated easily with self.theta
        temp = self._F, self._R, self._modifiedCorrMatrix, self.v
        self._F, self._R, self._modifiedCorrMatrix, self.v = [None] * 4
        super(AbstractKriging, self).save(filename, path)
        self._F, self._R, self._modifiedCorrMatrix, self.v = temp

    def _isCreated(self):
        """Checks if self.createSurrogateModel was run and the required values are set"""
        return self.v is not None and self.theta is not None

    isCreated = property(fget=_isCreated)


class Kriging(AbstractKriging):
    """Kriging class - takes at least two arguments: sampleX, sampleY.

    :param sampleX: is an array in which contains the sample points column by column (one parameter configuration = one column)
        Attention: sampleX is scaled to bounds. This module normalizes sampleX itself
    :param sampleY: is an array in which contains the scalar function values at the sample points
    :param lowerBounds: array with lower bounds of length self.p. Defaults to [0, 0, ...]
    :param upperBounds: array with upper bounds of length self.p. Defaults to [1, 1, ...]

    Optionally you can determine by the 3rd argument corr which correlation model will be used. By default, corr is 'cubic', for cubic correlation model,
    which is the numerically most stable one. But you can also choose 'exp' for exponential correlation model or 'gauss' for gaussian correlation model.
    By setting the 4th argument regress, you can determine which regression model will be used. It is 'const' by default, but you can also choose 'linear'
    for a linear regression.
    """

    def __init__(
        self,
        sampleX,
        sampleY,
        lowerBounds=None,
        upperBounds=None,
        corr="cubic",
        regress="const",
        parameterNames=None,
        resultNames=None,
        **kwargs,
    ):
        AbstractKriging.__init__(
            self, sampleX, sampleY, lowerBounds, upperBounds, corr, regress, parameterNames, resultNames
        )

        for key in kwargs:
            if not hasattr(self, key):
                raise DelisMMError(
                    'Setting unknown key "'
                    + key
                    + '" in class "'
                    + str(self.__class__)
                    + '" with name "'
                    + str(self)
                    + '"'
                )
            setattr(self, key, kwargs[key])


class HierarchicalKriging(AbstractKriging):
    """
    Hierarchical Kriging class - takes at least three arguments: sampleX, sampleY, lfKriging.
    :param sampleX: is an array in which contains the sample points column by column (one parameter configuration = one column)
        Attention: sampleX is scaled to bounds. This module normalizes sampleX itself
    :param sampleY: is an array in which contains the scalar function values at the sample points
    :param lfKriging: is an instance of Kriging or HierarchicalKriging class; model for the low-fidelity data.
    :param lowerBounds: array with lower bounds of length self.p. Defaults to [0, 0, ...]
    :param upperBounds: array with upper bounds of length self.p. Defaults to [1, 1, ...]

    Optionally you can determine by the 3rd argument corr which correlation model will be used.
    By default, corr is 'cubic', for cubic correlation model, which is the numerically most stable one.
    But you can also choose 'exp' for exponential correlation model or 'gauss' for gaussian correlation model.
    By setting the 4th argument regress, you can determine which regression model will be used.
    It is 'const' by default, but you can also choose 'linear'
    for a linear regression.
    """

    def __init__(
        self,
        sampleX,
        sampleY,
        lfKriging,
        lowerBounds=None,
        upperBounds=None,
        corr="cubic",
        regress="const",
        parameterNames=None,
        resultNames=None,
        **kwargs,
    ):
        self.lfKriging = lfKriging
        AbstractKriging.__init__(
            self,
            sampleX,
            sampleY,
            lowerBounds,
            upperBounds,
            corr,
            regress,
            parameterNames=parameterNames,
            resultNames=resultNames,
        )
        self.name = "hier-" + self.name

        for key in kwargs:
            if not hasattr(self, key):
                raise DelisMMError(
                    'Setting unknown key "'
                    + key
                    + '" in class "'
                    + str(self.__class__)
                    + '" with name "'
                    + str(self)
                    + '"'
                )
            setattr(self, key, kwargs[key])

    def _regressionVector(self, xNormalized):
        """See AbstractKriging for documentation"""
        regressionVector = super()._regressionVector(xNormalized)
        regressionVector[0] = self.lfKriging.callNormalized(xNormalized)[0]
        return regressionVector


if __name__ == "__main__":
    pass
