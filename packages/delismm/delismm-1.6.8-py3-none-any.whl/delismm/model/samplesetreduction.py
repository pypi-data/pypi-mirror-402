"""
This module is inteded to hande sampleX and sampleY values that may be reduced by sampleX/sampleY-columns and based on some criteria of the samples.

Created on 16.10.2017

@author: freu_se
"""

from collections import OrderedDict

import numpy as np
import pandas as pd


class SampleSetReducer:
    """classdoc"""

    def __init__(self, parameterNames, resultNames, nameToEqCriterionTuples=None, reduceParameterResultNames=None):
        """Initialization of SampleSetReducer

        Caution!! SampleX and SampleY are transposed to each other! sampleX.T matches sampleY

        :param parameterNames: list with names of the input parameters
        :param resultNames: list with names of the output parameters
        :param nameToEqCriterionTuples: list with tuples that define a input/output parameter and a value as equality criterion
            in order to remove rows from the dataset. (see test for an example)
        :param reduceParameterResultNames: list with input and/or output parameter names that should be removed
        """
        self.parameterNames = parameterNames
        self.resultNames = resultNames
        self.reduceParameterResultNames = reduceParameterResultNames
        self.nameToEqCriterionTuples = nameToEqCriterionTuples

    def getReducedSamples(self, sampleX, sampleY):
        """Method that reduces the given sampleX and sampleY"""
        # =======================================================================
        # setup dataframe
        # =======================================================================
        oDictInput = [(name, sampleColumn) for name, sampleColumn in zip(self.parameterNames, sampleX)]
        oDictInput += [(name, sampleColumn) for name, sampleColumn in zip(self.resultNames, zip(*sampleY))]
        samplesDf = pd.DataFrame(OrderedDict(oDictInput))

        # =======================================================================
        # use only row fulfilling the given criterion
        # =======================================================================
        if self.nameToEqCriterionTuples is not None:
            for name, criterion in self.nameToEqCriterionTuples:
                if not name in samplesDf.columns:
                    return sampleX, sampleY
                samplesDf = samplesDf[samplesDf[name] == criterion]

        # =======================================================================
        # reduce sample columns
        # =======================================================================
        parameterNames = self.parameterNames
        resultNames = self.resultNames
        if self.reduceParameterResultNames is not None:
            parameterNames = [
                parameterName
                for parameterName in parameterNames
                if parameterName not in self.reduceParameterResultNames
            ]
            resultNames = [
                resultName for resultName in resultNames if resultName not in self.reduceParameterResultNames
            ]
            newColumns = parameterNames + resultNames
            samplesDf = samplesDf.loc[:, newColumns]

        # =======================================================================
        # create result sample collections
        # =======================================================================
        sampleX = np.array(samplesDf.loc[:, parameterNames])
        sampleY = samplesDf.loc[:, resultNames].values.tolist()

        return sampleX.T, sampleY
