"""
Created on 13.04.2018

@author: geie_ma
"""

import numpy as np
import scipy as sp
from patme.service.logger import log
from scipy.optimize import differential_evolution

from delismm.model.customsystemfunction import BoundsHandler
from delismm.model.metrics import normalizedRootMeanSquareError
from delismm.model.surrogate import AbstractSurrogate
from delismm.service.exception import DelisMMError


class Rbf(AbstractSurrogate):
    """RBF class - takes at least two arguments: sampleX, sampleY.

    :param sampleX: is an array in which contains the sample points column by column (one parameter configuration = one column)
        Attention: sampleX is scaled to bounds. This module normalizes sampleX itself
    :param sampleY: is an array in which contains the scalar function values at the sample points
    :param lowerBounds: array with lower bounds of length self.p. Defaults to [0, 0, ...]
    :param upperBounds: array with upper bounds of length self.p. Defaults to [1, 1, ...]
    :param regress: type of regression model used (None, 'const', 'linear)
    :param rbfFunction: type of rbf form function ('multiquadric','inverse','gaussian','linear','cubic','quintic','thin_plate')
    :param parameterNames: list with parameter names with length of self.p
    """

    def __init__(
        self,
        sampleX,
        sampleY,
        lowerBounds=None,
        upperBounds=None,
        regress="linear",
        rbfFunction="multiquadric",
        parameterNames=None,
        resultNames=None,
    ):
        """RBF class that combines scipy.interpolate.Rbf with a regression model as well as an automated
        optimization of the regularization parameter as well as epsilon (only needed for multiquadric rbf)"""
        AbstractSurrogate.__init__(self, sampleX, sampleY, lowerBounds, upperBounds, parameterNames, resultNames)

        self.n = self.sampleXNormalized.shape[1]  # n - Number of sample points
        """n is the number of sample points"""
        self.p = self.sampleXNormalized.shape[0]  # p - Number of design variables
        """p is the dimension of the design space/ the number of model parameters"""
        self.regularizationParameter = None
        """parameter that allows relaxed fitting of rbf function (see smooth in scipy.interpolate.Rbf)"""
        self.doRegularizationParameterOpt = True
        """switch that performs the optimization of the regularization parameter"""
        self.numberOfOpt = 1
        """number of optimization runs to determine the regularization parameter"""
        self._scipyRbf = None
        """holds instance of scipy.interpolate.Rbf()"""
        self.rbfFunction = rbfFunction  #'multiquadric','inverse','gaussian','linear','cubic','quintic','thin_plate'
        """rbf form function type"""
        self.epsilon = None
        """parameter epsilon for multiquadric rbf function; epsilon will be estimated if None is provided
        (see scipy.interpolate.Rbf documentation)"""
        self.doEpsilonOpt = True
        """parameter epsilon for multiquadric rbf function can be optimzed instead of using the default value
        (see scipy.interpolate.Rbf documentation)"""
        self._regressCoeff = []
        """list of regression function coefficients"""
        self._sampleYRegressDelta = []
        """sampleY - regressionFunction(sampleX); empty if if self.regress=None"""
        self.name = "rbf"
        """surrogate model name"""

        # =======================================================================
        # regression method
        # can be one of [None, linear, const]
        # =======================================================================
        if regress == "linear":
            self.regress = "linear"
            log.debug("Use linear regression")
        elif regress == "const":
            self.regress = "const"
            log.debug("Use constant regression")
        elif regress == None:
            self.regress = None
            log.debug("Use no regression")
        else:
            raise DelisMMError("Only these values are applicable for parameter regress: [linear, const, None].")

        if self.rbfFunction not in ["multiquadric", "inverse", "gaussian", "linear", "cubic", "quintic", "thin_plate"]:
            raise DelisMMError(
                "Only these values are applicable for parameter regress: "
                "[multiquadric, inverse, gaussian, linear, cubic, quintic, thin_plate]."
            )

    def createSurrogateModel(self):
        """Creates the surrogate model"""
        # create regression model
        if self.regress:
            if self.regress == "linear":
                xData_linReg = self.sampleXNormalized.T
                xData_linReg = np.c_[xData_linReg, np.ones(xData_linReg.shape[0])]
                self._regressCoeff = np.linalg.lstsq(xData_linReg, self.sampleY)[0]
                self._sampleYRegressDelta = self.sampleY - [
                    sum(xData_linReg[pos] * self._regressCoeff) for pos in range(len(xData_linReg))
                ]
            elif self.regress == "const":
                self._regressCoeff = np.array([np.mean(self.sampleY)])
                self._sampleYRegressDelta = self.sampleY - self._regressCoeff[-1]

        # optimize the regularization parameter and epsilon
        if self.doRegularizationParameterOpt:
            optResults = []
            while len(optResults) + 1 <= self.numberOfOpt:
                log.info("Performing %d. parameter optimization for the RBF surrogate model" % (len(optResults) + 1))
                if self.rbfFunction == "multiquadric" and self.doEpsilonOpt:
                    bounds = [(0, 1), (1e-10, 10)]
                else:
                    bounds = [(0, 1)]
                optResult = differential_evolution(self._regularizationParameterFittnessFct, bounds)
                optResults.insert(-1, [optResult.fun] + list(optResult.x))
                if self.numberOfOpt > 1:
                    log.info("CV NRMSE / regParam / epsilon (opt): " + " / ".join([str(pos) for pos in optResults[-1]]))
            minNRMSEindex = list(np.array(optResults)[:, 0]).index(min(np.array(optResults)[:, 0]))
            self.regularizationParameter = optResults[minNRMSEindex][1]
            if self.rbfFunction == "multiquadric" and self.doEpsilonOpt:
                self.epsilon = optResults[minNRMSEindex][2]
            log.info(
                "--> BEST PARAMETERS (CV NRMSE / regParam / epsilon (opt)): "
                + " / ".join([str(pos) for pos in optResults[-1]])
            )
        elif self.regularizationParameter == None:
            raise DelisMMError(
                "If no regularization parameter optimization shall be performed, a regularization"
                "parameter has to be set manually."
            )

        if self.regress:
            yData = self._sampleYRegressDelta
        else:
            yData = self.sampleY
        self._scipyRbf = sp.interpolate.Rbf(
            *self.sampleXNormalized,
            yData,
            function=self.rbfFunction,
            smooth=self.regularizationParameter,
            epsilon=self.epsilon,
        )

    def _regularizationParameterFittnessFct(self, optParams):
        """Fittness function for the regularization parameter optimization.  returning the normalized root mean square error.
        :param optParams: list with optimization parameters [regularizationParameter, epsilon (optional)]
        :return: normalized root mean square error
        """
        if len(optParams) == 2:
            regularizationParameter, eps = optParams[0], optParams[1]
        #             if eps < 1E30 and eps > 0:
        #                 eps = 1E30
        #             if eps > -1E30 and eps < 0:
        #                 eps = -1E30
        else:
            regularizationParameter = optParams[-1]
            eps = None
        ys_rbf = []
        for pos in range(len(self.sampleY)):
            x_temp = np.delete(self.sampleXNormalized, pos, 1)
            if self.regress:
                y_temp = np.delete(self._sampleYRegressDelta, pos, 0)
            else:
                y_temp = np.delete(self.sampleY, pos, 0)
            rbf = sp.interpolate.Rbf(
                *x_temp, y_temp, function=self.rbfFunction, smooth=regularizationParameter, epsilon=eps
            )
            y_rbf = rbf(*self.sampleXNormalized[:, pos])
            ys_rbf.append(y_rbf)
        if self.regress:
            return normalizedRootMeanSquareError(self._sampleYRegressDelta, ys_rbf)
        else:
            return normalizedRootMeanSquareError(self.sampleY, ys_rbf)

    def __call__(self, xData):
        """Returns the function value at pointOfInterest.
        :param pointOfInterest: vector of length self.p within real bounds"""
        xData_Normalized = BoundsHandler.scaleTo01Static(np.array(xData), self.lowerBounds, self.upperBounds)
        return self.callNormalized(xData_Normalized)

    def callNormalized(self, xData_Normalized):
        """same as __call__ but uses normalized input samples"""
        ys = self._scipyRbf(*xData_Normalized)
        if self.regress == "linear":
            ys = ys + sum(np.append(xData_Normalized, 1) * self._regressCoeff)
        if self.regress == "const":
            ys = ys + self._regressCoeff[-1]
        return np.array([float(ys)])
