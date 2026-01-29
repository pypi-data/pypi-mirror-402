""""""

import os
from argparse import ArgumentParser

import numpy as np
from patme.service.logger import log

from delismm.model.doe import AbstractDOE
from delismm.model.metrics import relativeRootMeanSquareError, rootMeanSquareError
from delismm.model.surrogate import Kriging


def plotMetamodel(plotter, mm, lb, ub):
    plotSampeles = 150
    x = np.linspace(lb[0], ub[0], plotSampeles)
    y = np.linspace(lb[1], ub[1], plotSampeles)
    xv, yv = np.meshgrid(x, y)
    xv, yv = xv.flatten(), yv.flatten()
    z = np.array([mm([xVal, vVal]) for xVal, vVal in zip(xv, yv)])
    plotter.plotContour(xv, yv, z)


def writeData(outputDir, sampleX, sampleY):
    """write sampleX, sampleY"""
    sampleXFilename = os.path.join(outputDir, "sampleX_bounds.txt")
    if os.path.exists(sampleXFilename):
        log.info(f"Not writing sampleX file: already exists: {sampleXFilename}")
    else:
        np.savetxt(sampleXFilename, sampleX)
    sampleYFilename = os.path.join(outputDir, "sampleY.txt")
    if os.path.exists(sampleYFilename):
        log.info(f"Not writing sampleY file: already exists: {sampleYFilename}")
    else:
        np.savetxt(sampleYFilename, sampleY)


def readData(inputPath):
    """reads lowfi data"""
    sampleX = np.loadtxt(os.path.join(inputPath, "sampleX_bounds.txt"), encoding="utf8").T
    sampleY = AbstractDOE.ysFromFile(os.path.join(inputPath, "sampleY.pickle"))

    sampleX_new, sampleY_new = [], []
    for x, y in zip(sampleX.T, sampleY):
        if y[0] is None:
            continue
        sampleX_new.append(x)
        sampleY_new.append(y)
    sampleX = np.array(sampleX_new).T
    sampleY = sampleY_new

    lowerBounds = np.min(sampleX, axis=1)
    upperBounds = np.max(sampleX, axis=1)

    return sampleX, sampleY, lowerBounds, upperBounds


def createSingleKriging(lowFiX, lowFiy, lb, ub, name, parameterNames, log10SampleY):
    kriging = Kriging(
        lowFiX,
        lowFiy,
        lowerBounds=lb,
        upperBounds=ub,
        parameterNames=parameterNames,
        resultNames=[name],
        doRegularizationParameterOpt=True,
        corr="cubic",
        regress="linear",
        log10SampleY=log10SampleY,
        # optThetaGlobalAttempts=1,
    )
    kriging.createSurrogateModel()
    log.info(f"kriging {name}: theta {kriging.theta},regularization {kriging.regularizationParameter}")
    return kriging


def getKrigings(samplesDir, surrogateDir, parameterNames, resultNamesIndexesLog10, nameAddition=""):
    sampleX, sampleYAll, lb, ub = readData(samplesDir)
    sampleYAll = np.array(sampleYAll)

    mms = []
    for resultName, index, useLog10 in resultNamesIndexesLog10:
        mmName = f"lh2_tank_{nameAddition}{resultName}_v_2.0.pickle"
        readName = os.path.join(surrogateDir, f"tank_{resultName}.pickle")
        if os.path.exists(readName):
            mm = Kriging.load(readName)
        else:
            writeData(surrogateDir, sampleX, sampleYAll)
            sampleY = np.array(sampleYAll[:, index], dtype=np.float64)
            if useLog10:
                sampleY = np.log10(sampleY)
            mm = createSingleKriging(sampleX, sampleY, lb, ub, resultName, parameterNames, useLog10)
        mms.append(mm)

        saveName = os.path.join(surrogateDir, mmName)
        if os.path.exists(saveName):
            log.warning(f"Surrogate file already exists - not overriding: {saveName}")
        else:
            mm.save(saveName)
            with open(saveName.replace(".pickle", "_info.txt"), "w") as f:
                f.write(mm.getKrigingDocumentation())

    # accuracy
    for mm in mms:
        crossSampleY = mm.getCrossValidationValues()
        sample1, sample2 = (
            (np.power(10, mm.sampleY), np.power(10, crossSampleY)) if mm.log10SampleY else (mm.sampleY, crossSampleY)
        )
        rmse = rootMeanSquareError(sample1, sample2)
        rmsre = relativeRootMeanSquareError(sample1, sample2)
        np.savetxt(os.path.join(surrogateDir, mm.resultNames[0] + "_rmsre.txt"), sample2)
        log.info(f"\nRMSE: {rmse}\nRMSRE: {rmsre}")

    return mms


def main():
    ap = ArgumentParser(
        description="Calculate tank properties based on geometry and pressure. It calculates frpMass[kg], volume[dm^3], area[m^2], length[mm]."
    )
    ap.print_usage = ap.print_help  # redirecting the print_usage method to the extended print_help method
    ap.add_argument("radius", metavar="r", type=float, help="radius of the tank [mm]")
    ap.add_argument("lZylByR", metavar="lZylByR", type=float, help="length of zylindrical part by radius [-]")
    ap.add_argument("dp", metavar="dp", type=float, help="delta pressure [MPa]")
    ap.add_argument(
        "-d",
        "--dir",
        dest="dir",
        help="Path to the input files (samples or created surrogates)",
        metavar="DIR",
    )
    options = ap.parse_args()
    shape = "isotensoid"
    # shape = 'circle'
    if options.dir:
        runDir = options.dir
        if not os.path.exists(runDir):
            raise FileNotFoundError(f'given directory "{runDir}" does not exist.')
    else:
        runDir = f"C:\\PycharmProjects\\delis\\tmp\\2020_10_doe_{shape}_41\\"
    r, lZylByR, dp = options.radius, options.lZylByR, options.dp

    mms = getKrigings(runDir, shape)

    frpMass, volume, area, length = mms([r, lZylByR, dp])
    print(frpMass, volume, area, length)


if __name__ == "__main__":
    main()
