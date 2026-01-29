""""""

import numpy as np
from patme.service.systemutils import getTimeString
from scipy import interpolate
from scipy.interpolate import RegularGridInterpolator

from delismm.model.customsystemfunction import BoundsHandler, KrigingCorrelation, KrigingRegression
from delismm.model.surrogate import HierarchicalKriging, Kriging


class RegularGridInterpolatorContainer:
    """RegularGridInterpolator should behave like a kriging model"""

    def __init__(self, rgi, lb, ub):
        self.rgi = rgi
        self.lb = lb
        self.ub = ub

    def __call__(self, xi, method="linear"):
        return self.rgi([xi])[0]

    def callNormalized(self, poiNomalized):
        return [self(BoundsHandler.scaleToBoundsStatic(poiNomalized, self.lb, self.ub))]


def plotMetamodel(plotter, mm, lb, ub):
    plotSampeles = 150
    x = np.linspace(lb[0], ub[0], plotSampeles)
    y = np.linspace(lb[1], ub[1], plotSampeles)
    xv, yv = np.meshgrid(x, y)
    xv, yv = xv.flatten(), yv.flatten()
    z = np.array([mm([xVal, vVal]) for xVal, vVal in zip(xv, yv)])
    plotter.plotContour(xv, yv, z)


def plotHighFiSamples(plotter, vmm, mm):
    hfx = vmm.sampleX.T
    hfy = vmm.sampleY

    diffMmVmm = hfy - np.array([mm(poi) for poi in hfx])

    plotter.plotScatter(hfx[:, 0], hfx[:, 1], pointColors=diffMmVmm, label="hifi-lowfi")


def getInterp(inputPath, plotter):
    """returns interpolation function for lowfi data"""
    lowFi = np.loadtxt(inputPath + "082 C2 260 158_AOIcartCorr.txt")
    samplesPerDirection = int(np.sqrt(lowFi.shape[0]))

    plotter.plotContour(lowFi[:, 0], lowFi[:, 1], lowFi[:, 2])

    if 0:
        f = interpolate.interp2d(lowFi[:, 0], lowFi[:, 1], lowFi[:, 2], kind="cubic")
    else:
        data = lowFi[:, 2].reshape((samplesPerDirection, samplesPerDirection)).T
        f = RegularGridInterpolator(
            (lowFi[:samplesPerDirection, 0], lowFi[::samplesPerDirection, 1]),
            data,
            bounds_error=False,
            fill_value=0.0,
        )

    return f, np.min(lowFi[:, :2], axis=0), np.max(lowFi[:, :2], axis=0)


def readData(inputPath, plotter, useEvery):
    """reads lowfi data"""
    lowFi = np.loadtxt(inputPath + "082 C2 260 158_AOIcartCorr.txt")
    samplesPerDirection = int(np.sqrt(lowFi.shape[0]))

    plotter.plotContour(lowFi[:, 0], lowFi[:, 1], lowFi[:, 2])

    lowFiReshaped = np.reshape(
        lowFi, (int(lowFi.shape[0] / samplesPerDirection), int(lowFi.shape[0] / samplesPerDirection), 3)
    )
    lowFiReduced = lowFiReshaped[::useEvery, ::useEvery, :]
    lowFiX = np.reshape(lowFiReduced, (int((samplesPerDirection / useEvery) ** 2), 3))[:, :2].T
    lowFiy = np.reshape(lowFiReduced, (int((samplesPerDirection / useEvery) ** 2), 3))[:, 2]

    lowerBounds = np.min(lowFiX, axis=1)
    upperBounds = np.max(lowFiX, axis=1)

    return lowFiX, lowFiy, lowerBounds, upperBounds


def readDataHiFi(inputPath, plotter):
    """read highfi data"""
    highFi = np.loadtxt(inputPath + "082_Thermoelemente_Auswahl.txt")

    plotter.plotScatter(highFi[:, 0], highFi[:, 1])

    return highFi[:, :2], highFi[:, 3]


def createKrigingLowFi(lowFiX, lowFiy, savePath, lb, ub):
    kriging = Kriging(
        lowFiX,
        lowFiy,
        lowerBounds=lb,
        upperBounds=ub,
        parameterNames=["x", "y"],
        doRegularizationParameterOpt=False,
        optThetaGlobalAttempts=2,
    )
    kriging.createSurrogateModel()  # theta=[0.55175332, 0.73914592])
    kriging.save(f"kriging_model_{kriging.n}.pickle", savePath)

    print(kriging.theta, kriging.regularizationParameter)

    return kriging


def main():
    from delis.service.dataplotter import PlotGraphMatplotlib

    plotter = PlotGraphMatplotlib(shapeSubplots=(2, 3))
    inputPath = "C:\\PycharmProjects\\delis\\tmp\\temperatures\\"
    useEvery = 15

    if 0:
        lowFiX, lowFiy, lb, ub = readData(inputPath, plotter, useEvery)
        mm = createKrigingLowFi(lowFiX, lowFiy, inputPath, lb, ub)
        lb, ub = mm.lowerBounds, mm.upperBounds
    else:
        rgi, lb, ub = getInterp(inputPath, plotter)
        mm = RegularGridInterpolatorContainer(rgi, lb, ub)

    # highFi
    hfx, hfy = readDataHiFi(inputPath, plotter)
    plotter.activeNextSubplot()

    plotMetamodel(plotter, mm, lb, ub)
    plotter.activeNextSubplot()

    # create hf mm
    vmm = HierarchicalKriging(
        hfx.T,
        hfy,
        mm,
        lowerBounds=lb,
        upperBounds=ub,
        parameterNames=["x", "y"],
        doRegularizationParameterOpt=False,
        optThetaGlobalAttempts=2,
    )
    vmm.createSurrogateModel(theta=[3, 3])
    mmAtHf = [mm(poi) for poi in hfx]
    vmmAtHf = [vmm(poi) for poi in hfx]
    vmmMinMm = [vmm(poi) - mm(poi) for poi in hfx]

    plotMetamodel(plotter, vmm, lb, ub)
    plotHighFiSamples(plotter, vmm, mm)
    plotter.activeNextSubplot()

    # plot correlation model
    krigingCorr = KrigingCorrelation(vmm)
    plotMetamodel(plotter, krigingCorr, lb, ub)
    plotHighFiSamples(plotter, vmm, mm)
    plotter.activeNextSubplot()

    # plot regression model
    krigingReg = KrigingRegression(vmm)
    plotMetamodel(plotter, krigingReg, lb, ub)
    plotHighFiSamples(plotter, vmm, mm)
    plotter.activeNextSubplot()

    plotter.legend()
    plotter.show()


if __name__ == "__main__":
    main()
