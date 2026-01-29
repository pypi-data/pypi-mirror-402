"""
Created on 28.11.2016

@author: freu_se
"""

from collections import OrderedDict

import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
from patme.service.logger import log
from patme.service.stringutils import indent

from delismm.model.customsystemfunction import BoundsHandler
from delismm.model.doe import FullFactorialDesign
from delismm.model.samplecalculator import getY


class ModelPlotter:
    """This class is supposed to plot models of various kind.

    reqired attributes of models::

    - callable with vector of params as input, the output is a list where the first item is used
    - lowerBounds, upperBounds
    - name
    - parameterNames

    from delismm.model.customsystemfunction import ExampleFunction, ExampleFunctionModified
    from delis.service.dataplotter import PlotGraphMatplotlib
    lb, ub = OrderedDict([('testParameter', 0.0),('testParameter2', 0.0)]), OrderedDict([('testParameter', 1.0),('testParameter2', 1.0)])
    models = [ExampleFunction(lb, ub), ExampleFunctionModified(lb, ub)]
    plotter = PlotGraphMatplotlib(shapeSubplots=(1,2))
    mp = ModelPlotter(models, plotter)
    mp.samplingSize = 101
    mp.plotModel([m.name for m in models], ['testParameter','testParameter2'], [0.5,0.5])
    plotter.activeNextSubplot()
    mp.plotModel([m.name for m in models], ['testParameter'], [0.5,0.5], [0.,0.], [0.5,1.0])
    # plotter.show()
    plotter.closeFigure()
    """

    def __init__(self, models, plotInsance):
        """doc"""
        self.samplingSize = 101
        """number of ticks in 1 direction to evaluate the function to plot"""
        self.plotter = plotInsance
        self._plotData = []
        """Cache for data to be plot until it is plot. Structure of each line: [funcOrAttr, args, kwargs]"""
        self._setModels(models)

    def _setModels(self, models):
        """is called on initialization or after a reset"""
        if len(models) == 0:
            return
        self._modelDict = OrderedDict()
        self._firstModel = models[0]
        self._modelDict[self._firstModel.name] = models[0]
        for model in models[1:]:
            self.addModel(model)

    def resetModels(self, models):
        """deletes all actual models and uses the given models"""
        self._setModels(models)

    def addModel(self, model):
        """doc"""
        lb, ub = self.lowerBounds, self.upperBounds
        if not np.allclose(lb, model.lowerBounds) or not np.allclose(ub, model.upperBounds):
            raise ValueError("No matching bounds of these models: " + str(model[0].name, ", " + str(model.name)))
        if model.name in self._modelDict:
            raise ValueError('There are models with equal names: "' + str(model.name) + '"')
        self._modelDict[model.name] = model

    def plotModel(
        self,
        modelNames,
        parameterNames,
        nominalValues,
        lowerBounds=None,
        upperBounds=None,
        title="",
        plotKind=None,
        samplingSizes=None,
        lineTrace3d=False,
        legendLocation="upper right",
    ):
        """

        :param lineTrace3d: For 3d contour plots, lines of both parameters are plot, that depict the trace on the surface in
            respect to the nominal value of the other parameter respectively
        :param legendLocation: string, defining the legends location. One of these: ['best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center']
        """
        self.collectPlotData(
            modelNames,
            parameterNames,
            nominalValues,
            lowerBounds,
            upperBounds,
            title,
            plotKind,
            samplingSizes,
            lineTrace3d,
            legendLocation,
        )
        self.plotCachedData()

    def collectPlotData(
        self,
        modelNames,
        parameterNames,
        nominalValues,
        lowerBounds=None,
        upperBounds=None,
        title="",
        plotKind=None,
        samplingSizes=None,
        lineTrace3d=False,
        legendLocation="upper right",
    ):
        """doc"""
        lowerBounds, upperBounds = self._checkPlotModelInputs(parameterNames, nominalValues, lowerBounds, upperBounds)

        if samplingSizes is None:
            samplingSizes = [self.samplingSize] * len(modelNames)

        if plotKind is None:
            plotKind = self._getPlotKind(parameterNames)

        if not all([samplingSize == samplingSizes[0] for samplingSize in samplingSizes]):
            # different sampling size among the models. This does not work in one data frame
            for modelName, samplingSize in zip(modelNames, samplingSizes):
                self.collectPlotData(
                    [modelName],
                    parameterNames,
                    nominalValues,
                    lowerBounds,
                    upperBounds,
                    title,
                    plotKind,
                    [samplingSize],
                    lineTrace3d,
                )
            return

        df = self._getPlotDataFrame(modelNames, parameterNames, nominalValues, lowerBounds, upperBounds, samplingSizes)
        self._plotData.append(
            [self.plotter.plot, [df], {"kind": plotKind, "title": title, "legendKwArgs": {"loc": legendLocation}}]
        )

        if lineTrace3d:
            if plotKind != "contour3d":
                log.warning('Will not create lineTrace3d since the plot kind is not "contour3d"')
                return
            if len(parameterNames) != 2:
                raise Exception("There must be excatly 2 parameters given for the lineTrace3d")
            allParameterNames = self._firstModel.parameterNames
            # first param
            df = self._getPlotDataFrame(
                modelNames, [parameterNames[0]], nominalValues, lowerBounds, upperBounds, samplingSizes
            )
            otherParameterNominalValue = nominalValues[allParameterNames.index(parameterNames[1])]

            self._plotData.append(
                [
                    self.plotter.plotLine3D,
                    (
                        df[parameterNames[0]],
                        [otherParameterNominalValue] * len(df[parameterNames[0]]),
                        df[modelNames[0]],
                    ),
                    {"legendKwArgs": {"loc": legendLocation}},
                ]
            )
            # second param
            df = self._getPlotDataFrame(
                modelNames, [parameterNames[1]], nominalValues, lowerBounds, upperBounds, samplingSizes
            )
            otherParameterNominalValue = nominalValues[allParameterNames.index(parameterNames[0])]
            self._plotData.append(
                [
                    self.plotter.plotLine3D,
                    [
                        [otherParameterNominalValue] * len(df[parameterNames[1]]),
                        df[parameterNames[1]],
                        df[modelNames[0]],
                    ],
                    {"legendKwArgs": {"loc": legendLocation}},
                ]
            )

    def plotCachedData(self):
        """doc"""
        for funcOrAttr, args, kwargs in self._plotData:
            if hasattr(funcOrAttr, "__call__"):
                funcOrAttr(*args, **kwargs)
            else:
                setattr(self.plotter, funcOrAttr, args[0])
        self._plotData = []

    def _getPlotKind(self, parameterNames):
        """doc"""
        if len(parameterNames) == 1:
            return "line"
        if isinstance(self.plotter.ax, Axes3D):
            return "contour3d"
        return "contour"

    def _getPlotDataFrame(self, modelNames, parameterNames, nominalValues, lowerBounds, upperBounds, samplingSizes):
        """Creates the data frame for each model by calling the model at a full factorial design(ffd) grid.

        A sampleX array is created, that contains nominals, where no parameter variation is done and
        the ffd values where the parameter is in parameterNames. Then, the model values are calculated and
        appended to the dataframe
        """
        allParameterNames = self._firstModel.parameterNames
        lowerBoundsPlot = [lowerBounds[allParameterNames.index(parameterName)] for parameterName in parameterNames]
        upperBoundsPlot = [upperBounds[allParameterNames.index(parameterName)] for parameterName in parameterNames]

        dfDict = OrderedDict()

        # sample y
        for modelName, samplingSize in zip(modelNames, samplingSizes):
            doe = FullFactorialDesign(samplingSize ** len(parameterNames), len(parameterNames))
            sampleXToInclude = BoundsHandler.scaleToBoundsStatic(
                doe.sampleXNormalized, lowerBoundsPlot, upperBoundsPlot
            )
            sampleX = self._getSampleX(parameterNames, nominalValues, dfDict, sampleXToInclude)
            if not modelName in self._modelDict:
                raise ValueError('Model with name "' + str(modelName) + '" does not exist.')
            model = self._modelDict[modelName]
            sampleY = getY(sampleX, model, verbose=False)
            dfDict[modelName] = [sample[0] for sample in sampleY]
            log.debug(
                "plot function [{}] with parameter(s) [{}], nominal(s) [{}] using these sampleX:\n{}\nand sampleY\n{}".format(
                    modelName, parameterNames, nominalValues, indent(sampleX, delim=" "), indent(sampleY, delim=" ")
                )
            )
        return pd.DataFrame(dfDict)

    def plotSurrogateSamples(
        self,
        modelNames,
        parameterNames,
        nominalValues,
        lowerBounds=None,
        upperBounds=None,
        title="",
        plotKind=None,
        sampleCorrThresholds=None,
        legendLocation="upper right",
    ):
        """the models with name modelNames must have attributes "sampleX" and "sampleY"!

        :param modelNames: list of names that must be included in the keys of self._modelDict
        :param parameterNames: list of parameter names that are used in each model
        :param nominalValues: list of floats defining the nominal values of unused parameters.
            It has the length of all parameters, so each parameter must have a nominal value
        :param sampleCorrThresholds: list of thresholds for the correlation values
            of the samples. Samples with a correlation value of less than this threshold will be omitted.
        """
        self.collectPlotDataSurrogateSamples(
            modelNames,
            parameterNames,
            nominalValues,
            lowerBounds,
            upperBounds,
            title,
            plotKind,
            sampleCorrThresholds,
            legendLocation,
        )
        self.plotCachedData()

    def collectPlotDataSurrogateSamples(
        self,
        modelNames,
        parameterNames,
        nominalValues,
        lowerBounds=None,
        upperBounds=None,
        title="",
        plotKind=None,
        sampleCorrThresholds=None,
        legendLocation="upper right",
    ):
        """doc"""
        if sampleCorrThresholds is None:
            sampleCorrThresholds = [0.0] * len(modelNames)
        for modelName, sampleCorrThreshold in zip(modelNames, sampleCorrThresholds):
            if plotKind is None:
                plotKind = self._getPlotKind(parameterNames)
            df = self._getPlotDataFrameForSurrogateSamples(
                modelName, parameterNames, nominalValues, lowerBounds, upperBounds, sampleCorrThreshold
            )
            if len(df) == 0:
                log.info("No samples with a correlation higher than " + str(sampleCorrThreshold))
                return
            log.debug("sample dataframe\n" + str(df))
            # plot samples
            usedDf = df
            if plotKind == "contour3d":
                usedPlotKind = "scatter3d"
            else:
                usedPlotKind = "scatter"
                if plotKind == "contour":
                    usedDf = df.drop(usedDf.columns[2:-1], axis=1)
            self._plotData.append(
                [
                    self.plotter.plot,
                    [usedDf],
                    {"kind": usedPlotKind, "title": title, "legendKwArgs": {"loc": legendLocation}},
                ]
            )
            # plot lines
            if plotKind == "line":
                allXAndZ = [([df.iloc[rowIndex, 0]] * 2, df.iloc[rowIndex, 1:3]) for rowIndex in range(len(df))]
                for x, z in allXAndZ:
                    self._plotData.append(["color", ["gray"], {}])
                    self._plotData.append(
                        [self.plotter.plotLine, [x, z], {"label": None, "legendKwArgs": {"loc": legendLocation}}]
                    )
            elif plotKind == "contour3d":
                allXAndZ = [
                    ([df.iloc[rowIndex, 0]] * 2, [df.iloc[rowIndex, 1]] * 2, df.iloc[rowIndex, 2:4])
                    for rowIndex in range(len(df))
                ]
                for x, y, z in allXAndZ:
                    self._plotData.append(["color", ["gray"], {}])
                    self._plotData.append(
                        [self.plotter.plotLine3D, [x, y, z], {"label": None, "legendKwArgs": {"loc": legendLocation}}]
                    )

    def _getPlotDataFrameForSurrogateSamples(
        self, modelName, parameterNames, nominalValues, lowerBounds, upperBounds, sampleCorrThreshold
    ):
        """Creates the data frame for each model by collecting the proper samples from the surrogate.

        A sampleX array is created, that contains nominals, where no parameter variation is done and
        the ffd values where the parameter is in parameterNames.
        """
        model = self._modelDict[modelName]
        allParameterNames = model.parameterNames
        dfDict = OrderedDict()
        lowerBoundsPlot, upperBoundsPlot = [], []

        # plot sample x
        for parameterName in parameterNames:
            parameterIndex = allParameterNames.index(parameterName)
            lowerBoundsPlot.append(lowerBounds[parameterIndex])
            upperBoundsPlot.append(upperBounds[parameterIndex])
            dfDict[parameterName] = model.sampleX[parameterIndex]

        # sample y projected
        plotSampleX = self._getSampleX(parameterNames, nominalValues, {}, np.array(list(dfDict.values())))

        sampleY = getY(plotSampleX, model, verbose=False)
        dfDict[modelName + "_project"] = [sample[0] for sample in sampleY]

        dfDict[modelName] = model.sampleY

        # calculate correlation values
        plotSampleXNormalized = BoundsHandler.scaleTo01Static(plotSampleX, self.lowerBounds, self.upperBounds)
        sampleXNormalized = BoundsHandler.scaleTo01Static(model.sampleX, self.lowerBounds, self.upperBounds)
        correlations = model.correlationFunctionNSamples(np.array(plotSampleXNormalized.T), sampleXNormalized.T)[0]
        dfDict["scatterColor"] = correlations

        df = pd.DataFrame(dfDict)

        # drop samples that are out of plot bounds
        lowerBoundsPlot, upperBoundsPlot = np.array(lowerBoundsPlot), np.array(upperBoundsPlot)
        inBounds = 1
        for parameterName, lowerBoundPlot, upperBoundPlot in zip(parameterNames, lowerBoundsPlot, upperBoundsPlot):
            inBounds &= (lowerBoundPlot - 1e-8 < df[parameterName]) & (df[parameterName] < upperBoundPlot + 1e-8)
        outOfBoundsIndex = inBounds[inBounds == False].index
        df.drop(outOfBoundsIndex, inplace=True)

        # drop samples that have a lower correlation value than the given threshold
        lowCorrelation = df["scatterColor"] < sampleCorrThreshold
        lowCorrelationIndex = lowCorrelation[lowCorrelation == True].index
        df.drop(lowCorrelationIndex, inplace=True)
        df.index = pd.RangeIndex(0, len(df), 1)

        # add two samples with correlation color zero and one in order to get the color of the plot range correct
        # they shold be plot first, in order to be replot by the real correlation
        if len(df):
            df = df.iloc[::-1]
            df = df.append(df.loc[0], ignore_index=True)  # copy last row, add it to df
            df = df.append(df.loc[len(df) - 1], ignore_index=True)  # copy last row, add it to df
            df = df.iloc[::-1]
            df["scatterColor"][len(df) - 2] = sampleCorrThreshold
            df["scatterColor"][len(df) - 1] = 1.0

        return df

    def _getSampleX(self, parameterNames, nominalValues, dfDict, sampleXToInclude):
        """Creates a sampleX array, that contains nominals, where no parameter variation is done and
        the values of sampleXToInclude where the parameter is in parameterNames."""
        allParameterNames = self._firstModel.parameterNames
        numberOfSamples = len(sampleXToInclude[0])
        sampleX = np.array([nominalValues] * numberOfSamples).T
        for parameterName, samples in zip(parameterNames, sampleXToInclude):
            parameterIndex = allParameterNames.index(parameterName)
            dfDict[parameterName] = samples
            sampleX[parameterIndex, :] = samples
        return sampleX

    def _checkPlotModelInputs(self, parameterNames, nominalValues, lowerBounds, upperBounds):
        """doc"""
        if len(nominalValues) != self.p:
            raise ValueError("Size of nominal values is wrong.")
        if lowerBounds is None:
            lowerBounds = self.lowerBounds
        elif len(lowerBounds) != self.p:
            raise ValueError("Size of lower bounds is wrong.")
        elif np.any(self.lowerBounds - np.abs(self.lowerBounds) * 0.02 > lowerBounds):
            raise ValueError("Given bounds are lower than the models lower bounds.")
        if upperBounds is None:
            upperBounds = self.upperBounds
        elif len(upperBounds) != self.p:
            raise ValueError("Size of upper bounds is wrong.")
        elif np.any(self.upperBounds + np.abs(self.upperBounds) * 0.02 < upperBounds):
            raise ValueError("Given bounds are greater than the models upper bounds.")
        if len(parameterNames) > 2:
            raise ValueError("Can only plot 2 parameters")
        return lowerBounds, upperBounds

    def _getLowerBounds(self):
        """doc"""
        return self._firstModel.lowerBounds

    def _getUpperBounds(self):
        """doc"""
        return self._firstModel.upperBounds

    def _getParameterCount(self):
        """doc"""
        return len(self.lowerBounds)

    p = property(fget=_getParameterCount)
    lowerBounds = property(fget=_getLowerBounds)
    upperBounds = property(fget=_getUpperBounds)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
#     from delismm.model.customsystemfunction import ExampleFunction, ExampleFunctionModified
#     from delis.service.dataplotter import PlotGraphMatplotlib
#     lb, ub = OrderedDict([('testParameter', 0.0),('testParameter2', 0.0)]), OrderedDict([('testParameter', 1.0),('testParameter2', 1.0)])
#     models = [ExampleFunction(lb, ub)]#, ExampleFunctionModified(lb, ub)]
#     plotter = PlotGraphMatplotlib(shapeSubplots=(2,2), is3dAxes=[False,True,False,False])
#     mp = ModelPlotter(models, plotter)
#     mp.samplingSize = 101
#     mp.plotModel([m.name for m in models], ['testParameter','testParameter2'], [0.5,0.5], [0.,0.], [0.65,0.65])
#     plotter.activeNextSubplot()
#     mp.plotModel([m.name for m in models], ['testParameter','testParameter2'], [0.5,0.5], [0.,0.], [0.65,0.65])
#     plotter.activeNextSubplot()
#     mp.plotModel([m.name for m in models], ['testParameter'], [0.5,0.5], [0.,0.], [0.5,1.0])
#     plotter.show()
#     plotter.closeFigure()
