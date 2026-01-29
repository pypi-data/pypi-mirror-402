"""
Created on 17.02.2016

@author: freu_se
"""

import itertools
import re
from datetime import datetime

from delismm.service.exception import DelisMMError


def getTimeString(useMilliSeconds=False):
    """returns a time string of the format: yyyymmdd_hhmmss"""
    dt = datetime.now()
    return dt.strftime("%Y%m%d_%H%M%S") + ("_{}".format(dt.microsecond) if useMilliSeconds else "")


def exportSampleDataForOptimus(sampleX, sampleY, xKeys, yKeys, filePath=None, outputType="training"):
    """Converts sample data into input test or training data for the program Optimus.
    :param sampleX: is an array in which contains the sample points column by column (one parameter configuration = one column)
    :param sampleY: is an array in which contains the scalar function values at the sample points
    :param xKeys: list of sampleX parameters (len(list) = number of columns of sampleX)
    :param yKeys: list of sampleY parameters (len(list) = len(sampleY))
    :param filePath: file path for output file (outputType will be added)
    :param outputType: switch to choose between training or test data output
    """
    if not filePath:
        filePath = "optimusInput.dat"
    filePath = filePath[: filePath.rfind(".")] + "_" + outputType + filePath[filePath.rfind(".") :]

    if outputType == "training":
        output = str(len(xKeys)) + "\n" + str(len(yKeys)) + "\n"
        output += " ".join([str(key) for key in xKeys + yKeys]) + "\n"
    elif outputType == "test":
        output = ""
    else:
        raise DelisMMError("outputType: " + outputType + " not supported. Use [training, test].")

    for xData, yData in zip(sampleX.T, sampleY):
        output += " ".join([str(x) for x in xData]) + " "
        output += str(yData) + "\n"
    f = open(filePath, "w")
    f.write(output)
    f.close()


def extractTrailingNumber(folderName):
    """
    Extracts the trailing number from a folder name.

    :param folderName: The name of the folder.
    :return The extracted trailing number as an integer. Throws an error if no trailing integer is found.
    """
    match = re.search(r"\d+$", folderName)
    if match is None:
        raise DelisMMError(f"Couldn't find process number at the end of {folderName}")
    return int(match.group())


if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=1)
