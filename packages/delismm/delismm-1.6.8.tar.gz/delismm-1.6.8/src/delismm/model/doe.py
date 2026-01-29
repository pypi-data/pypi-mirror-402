# -*- coding:utf-8 -*-
# Copyright (C) 2013 Deutsches Zentrum fuer Luft- und Raumfahrt(DLR, German Aerospace Center) <www.dlr.de>
"""
Created on 23.04.2013
@author: saue_a0
"""
import itertools
import os
import pickle

import numpy as np
from patme.service.logger import log
from patme.service.stringutils import indent

from delismm.model.customsystemfunction import BoundsHandler
from delismm.model.samplecalculator import getY
from delismm.service.exception import DelisMMError


class DOEQuality:
    """Assesses a DOEs quality

    [1]M. D. Morris and T. J. Mitchell, "Exploratory designs for computational experiments," Journal of statistical planning and inference, vol. 43, no. 3, pp. 381–402, 1995.


    """

    @staticmethod
    def jd(sampleXNormalized):
        """computes the multiplicity array and the distinct distances of an LH#
        @param lhs the sampling plan
        """

        lhs = sampleXNormalized.T
        n, p = lhs.shape
        first = np.zeros((n * (n - 1) // 2, p))
        second = np.zeros((n * (n - 1) // 2, p))

        start = 0
        for i in range(n - 1):
            length = n - i - 1
            first[start : start + length, :] = np.zeros((length, p)) + lhs[i]
            second[start : start + length, :] = lhs[i + 1 :, :]
            start += length
        d = np.linalg.norm(first - second, axis=1)

        distinct, J = np.lib.arraysetops.unique(d, return_counts=True)
        return J, distinct

    @staticmethod
    def mm(sampleXNormalized):
        """Computes the maximin metric
        computes sampling plan quality according to Morris&Mitchell
        @param lhs the sampling plan"""
        J, d = DOEQuality.jd(sampleXNormalized)
        return np.sum(np.multiply(J, d**-2)) ** 0.5


class AbstractDOE:
    """Abstract class with interface specifications for DOE methods"""

    def __init__(self, n, p):
        """Initializes the DOE parameters n and p, where n is the number of sample points and p is the dimension of the design space"""
        self.n = n  # n is the desired number of points
        self.p = p  # p is the number of design variables, thus the dimension of design space
        self.sampleXNormalized = None
        """matrix with samples created with length [p, n]
        This matrix is always normalized [0,1]"""

    def _runDOE(self):
        """Method that creates a DOE with n sample points for the unit cube [0,1]^p"""
        raise NotImplementedError("This method must be implemented in a subclass")

    def getY(self, targetFunctionInstance, verbose=True):
        """see getY as description"""
        sampleX = BoundsHandler.scaleToBoundsStatic(
            self.sampleXNormalized, targetFunctionInstance.lowerBounds, targetFunctionInstance.upperBounds
        )
        return np.array(getY(sampleX, targetFunctionInstance, verbose))

    def xToFile(self, filename):
        """Method that saves sample points to a given path (but not the function values!)
        :param filename: filename of the file in which the sample points shall be saved
        """
        self.__class__.xToFileStatic(filename, self.sampleXNormalized)

    @staticmethod
    def xToFileStatic(filename, sampleXNormalized):
        """Method that saves sample points to a given path (but not the function values!)
        :param filename: filename of the file in which the sample points shall be saved
        """
        np.savetxt(filename, sampleXNormalized.T)

    @staticmethod
    def yToFile(filename, targetFunctionInstance, sampleY):
        """Saves the function values of the sample points to a given path (but not the sample points!).
        :param filename: filename of the file in which the function values shall be saved
        :param targetFunctionInstance: instance of a delismm.model.customsystemfunction class
            or a sub class of it.
        :param sampleY: sampleY that should be saved
        """
        header = ""
        if targetFunctionInstance is not None:
            header += str(targetFunctionInstance.__class__) + "\n"
            if targetFunctionInstance.bounds:
                header += "Parameters: \n" + indent(targetFunctionInstance.bounds)
                if hasattr(targetFunctionInstance, "resultNames"):
                    header += "Result values: \n{}".format(", ".join(targetFunctionInstance.resultNames)) + "\n"
        header = "# " + header.replace("\n", "\n# ") + "\n"
        body = indent(sampleY, delim=" ")
        with open(filename, "w") as f:
            f.write(header + body)
        pickleFilename = os.path.splitext(filename)[0] + ".pickle"
        with open(pickleFilename, "wb") as f:
            pickle.dump(sampleY, f)

    @staticmethod
    def ysFromFile(sampleYFile, targetFunctionInstance=None):
        """Reads the function values of the sample points from a given path (but not the sample points!).
        :param sampleYFile: filename of the file in which the function values shall be read
        :param targetFunctionInstance: instance of a delismm.model.customsystemfunction class
            or a subclass of it.
        :return: sampleY that should be read
        """
        if not os.path.exists(sampleYFile):
            log.info("Load sampleY failed. This path and file does not exist: " + sampleYFile)
            return None
        if os.path.exists(sampleYFile) and ".pickle" in sampleYFile:
            with open(sampleYFile, "rb") as f:
                sampleY = pickle.load(f)
            if targetFunctionInstance is not None and hasattr(targetFunctionInstance, "resultNames"):
                if sampleY[0] is None or len(sampleY[0]) != len(targetFunctionInstance.resultNames):
                    log.info(
                        f"sampleY does not contain same number of results as given target function. \
                                 SampleY[0]: {sampleY[0]}, target function result names: {targetFunctionInstance.resultNames}"
                    )
                    return []
            log.info("Read sampleY, count: " + str(len(sampleY)))
            return sampleY
        else:
            # old version
            ys = np.loadtxt(sampleYFile)
            if ys.ndim == 1:
                # old format
                ys = ys.reshape((len(ys), 1))
            return ys.tolist()

    def xyToFile(self, filename, sampleY, headerNames=None, lb=None, ub=None, scaleToBounds=False):

        allSamples = [] if headerNames is None else [headerNames]
        allSamples.extend(self._getSamplesForXYToFile(sampleY, lb, ub, scaleToBounds))
        with open(filename, "w") as f:
            f.write(indent(allSamples, delim="  ", hasHeader=headerNames is not None))

    def _getSamplesForXYToFile(self, sampleY, lb=None, ub=None, scaleToBounds=False):
        """Saves the sample points to a given path.
        :param sampleY: if you already have evaluated your sample points, you don't have to evaluate them
            again. Just pass the function values as the parameter sampleY.
        :param lb: lower bounds, dict{key:lowerbound}
        :param ub: upper bounds, dict{key:upperbound}
        :param scaleToBounds: Flag if sampleXNormalized should be scaled to original bounds
        :return: list with all samples
        """
        allSamples = []
        sampleX = (
            self.sampleXNormalized
            if not scaleToBounds
            else BoundsHandler.scaleToBoundsStatic(self.sampleXNormalized, list(lb.values()), list(ub.values()))
        )
        for inputSample, outputSample in zip(sampleX.T, sampleY):
            if hasattr(outputSample, "__iter__"):
                allSamples.append(list(inputSample) + list(outputSample))
            else:
                allSamples.append(list(inputSample) + list([outputSample]))
        return allSamples

    @staticmethod
    def xyToFileForPgfPlotsStatic(samples, filename, numberOfSplits=None, wrapFunc=None):
        """Creates a file writing the samples in the format for pgfplot input files.

        :param samples: some matrix-like iterable. It is the matrix of samples in the transponed form as doe.sampleXNormalized or not normalized
        :param filename: filename where the new file will be created
        :param numberOfSplits: in case of a full factorial design, this is the number of splits in each dimension
        :param wrapFunc: function that can be used to modify each element in samples while it is put in the list
        """
        samples = list(samples)
        if numberOfSplits is not None:
            # if splits are given, a full factorial design is assumed, then a countour plot is possibly used, scatter plot otherwise
            for sampleIndex in range(len(samples) - numberOfSplits, 0, -1 * numberOfSplits):
                samples.insert(sampleIndex, ["", ""])
        kwargs = {"delim": "  "}
        if wrapFunc is not None:
            kwargs["wrapfunc"] = wrapFunc
        with open(filename, "w") as f:
            f.write(indent(samples, **kwargs))

    def __add__(self, otherDoeOrSampleXNormalized):
        """Adds another DOE or additional Samples with this DOE creating a new class."""
        if isinstance(otherDoeOrSampleXNormalized, AbstractDOE):
            p = otherDoeOrSampleXNormalized.p
            n = self.n + otherDoeOrSampleXNormalized.n
            additionalSamples = otherDoeOrSampleXNormalized.sampleXNormalized
        elif isinstance(otherDoeOrSampleXNormalized, np.ndarray):
            p = otherDoeOrSampleXNormalized.shape[0]
            n = self.n + otherDoeOrSampleXNormalized.shape[1]
            additionalSamples = otherDoeOrSampleXNormalized
        else:
            raise DelisMMError("The given parameter must be either a doe or a numpy array")
        if p != self.p:
            raise DelisMMError("The given doe has a different number of parameters that this doe.")
        newSampleXNormalized = np.zeros((self.p, n))
        newSampleXNormalized[:, : self.n] = self.sampleXNormalized
        newSampleXNormalized[:, self.n :] = additionalSamples
        newDoe = AbstractDOE(n, self.p)
        newDoe.sampleXNormalized = newSampleXNormalized
        return newDoe

    @staticmethod
    def latinizeSampleXNormalized(sampleXNormalized):
        """Latinizes the given samples. Each sample point must be set on a latin hypercube grid.

        See chapter 4 in
        [1] Y. Saka, M. Gunzburger, and J. Burkardt, "Latinized, improved LHS, and CVT point sets in hypercubes," International Journal of Numerical Analysis and Modeling, vol. 4, no. 3–4, pp. 729–743, 2007.
        """
        samples = sampleXNormalized.T
        n, p = samples.shape
        indicies = range(n)
        for k in range(p):
            sortVector = samples[:, k]
            indicies, samples = zip(
                *[(index, sample) for _, index, sample in sorted(zip(sortVector, indicies, samples))]
            )
            samples = np.array(samples)
            samples[:, k] = np.linspace(0, 1, n)

        # sort for initial index
        samples = np.array([sample for _, sample in sorted(zip(indicies, samples))])
        return samples.T

    @staticmethod
    def joinDoeResults(doeDirs, targetDoeDir, targetFunction=None, parameterNames=None):
        """combines sampleX and sampleY from inputDirs and puts them in targetDir"""
        xs = []
        ys = []
        for dirName in doeDirs:
            xs.extend(DOEfromFile(os.path.join(dirName, "sampleX_bounds.txt")).sampleXNormalized.T)
            ys.extend(DOEfromFile.ysFromFile(os.path.join(dirName, "sampleY.pickle")))

        sampleX, sampleY = [], []
        for x, y in zip(xs, ys):
            if y[0] is None:
                continue
            sampleX.append(x)
            sampleY.append(y)

        sampleX = np.array(sampleX).T
        doe = AbstractDOE(*sampleX.shape)
        doe.sampleXNormalized = sampleX  # not normalized
        doe.xToFile(os.path.join(targetDoeDir, "sampleX_bounds.txt"))
        doe.yToFile(os.path.join(targetDoeDir, "sampleY.txt"), targetFunction, sampleY)
        doe.xyToFile(
            os.path.join(targetDoeDir, "full_doe.txt"),
            sampleY,
            headerNames=([] if parameterNames is None else parameterNames)
            + ([] if targetFunction is None else targetFunction.resultNames),
        )


class DOEfromFile(AbstractDOE):
    def __init__(self, path):
        """Reads sample points from file
        :param path: path of the file
        """
        if not os.path.exists(path):
            raise DelisMMError("This path does not exist: " + path)
        self.path = path
        self.sampleXNormalized = self._runDOE()
        log.debug(
            "sampleXNormalized = \n" + indent(self.sampleXNormalized) + " type: " + str(type(self.sampleXNormalized))
        )
        self.n = self.sampleXNormalized.shape[1]
        self.p = self.sampleXNormalized.shape[0]

    def _runDOE(self):
        """See AbstractDOE for documentation"""
        newSampleXNormalized = np.loadtxt(self.path)
        if len(newSampleXNormalized.shape) == 1:
            # if p == 1 then numpy writes only sampleXNormalized[:,] to file
            return np.array([newSampleXNormalized])
        else:
            return newSampleXNormalized.T


class MonteCarlo(AbstractDOE):
    """Generates a random sample set [0,..,1]^p, where p is the number of design variables."""

    def __init__(self, n, p):
        AbstractDOE.__init__(self, n, p)
        self.sampleXNormalized = self._runDOE()

    def _runDOE(self):
        """See AbstractDOE for documentation"""
        return np.random.rand(self.p, self.n)


class LatinHypercube(AbstractDOE):
    """Generates a random Latin Hypercube within [0,..,1]^p, where p is the number of design variables."""

    def __init__(self, n, p):
        AbstractDOE.__init__(self, n, p)
        self.sampleXNormalized = self._runDOE()

    def _runDOE(self):
        """See AbstractDOE for documentation"""

        sampleXNormalized = np.zeros((self.p, self.n))  # Erzeuge zunaechst eine p-dim Liste mit Samplepoints
        for i in range(self.p):  # Fuer jede der Designvariablen erstelle
            x = np.arange(self.n)  # Vektor mit Zahlen von 0 bis n-1
            np.random.shuffle(x)  # shuffle des Vektors
            x = x / float(self.n - 1)
            sampleXNormalized[i, :] = x
        # In sampleXNormalized stehen nun Spaltenweise die Koordinaten der Samplepoints, i-th sample-coordinates: sampleXNormalized[:,i]
        return sampleXNormalized


class FullFactorialDesign(AbstractDOE):
    """Generates a full factorial design within [0,..,1]^p

    :param n: number of samples. This parameter might be adjusted if n!=i^p for i=1..inf
            If n does not satisfy the equation the next lower value is used
    """

    def __init__(self, n, p):
        if p == 0:
            n = 0
        numberOfSplits = 1
        while numberOfSplits**p < n + 1:
            numberOfSplits += 1
        numberOfSplits -= 1
        n = numberOfSplits**p
        self.numberOfSplits = numberOfSplits
        AbstractDOE.__init__(self, n, p)
        self.sampleXNormalized = self._runDOE()

    def _runDOE(self):
        sampleXNormalized = np.array(
            [it.flatten() for it in np.meshgrid(*([np.linspace(0.0, 1.0, self.numberOfSplits)] * self.p))]
        )
        # somehow meshgrid confuses first and second axes
        if self.p > 1:
            sampleXNormalized[:2, :] = np.array([sampleXNormalized[1, :], sampleXNormalized[0, :]])
        return sampleXNormalized

    def _runDOEOld(self):
        """doc"""
        sampleXNormalized = np.zeros((self.p, self.numberOfSplits**self.p))
        j = 0
        # product returns all combinations of Listobjects in [] with repeats and return length equal to 'repeat'
        for L in itertools.product(np.linspace(0.0, 1.0, self.numberOfSplits), repeat=self.p):
            sampleXNormalized[:, j] = L
            j += 1
        return sampleXNormalized

    @staticmethod
    def isFFDSamples(sampleX, lowerBounds, upperBounds):
        """Returns True if the given samples are based on a full factorial design"""
        sampleXNormalized = BoundsHandler.scaleTo01Static(sampleX, lowerBounds, upperBounds)
        numberOfParameters, numberOfSamples = sampleXNormalized.shape
        first = sampleXNormalized[:, 0]
        last = sampleXNormalized[:, -1]
        if not np.allclose(first, np.zeros_like(first)) or not np.allclose(last, np.ones_like(first)):
            return False
        numberOfSplits = 2
        while numberOfSplits**numberOfParameters < numberOfSamples:
            numberOfSplits += 1
        if numberOfSplits**numberOfParameters != numberOfSamples:
            return False
        return True


class ScreeningDoe(AbstractDOE):
    """Morris' algorithm(1991) described in Forrester: "Engineering Design via Surrogate Modelling" chapter 1.3.1.

    :param n: number of samples. This parameter might be adjusted if n != (p+1)*i for i=1..inf
            If n does not satisfy the equation the next lower value is used. In the book this parameter is r * (self.p+1) = self.n
    :param p: number of design parameters. In the book this parameter is "k"
    :param xi: elementary effect step length factor.
    :param l: number of discrete levels along each dimension. In the book this parameter is "p"


    """

    def __init__(self, n, p, xi=1, l=21):
        n = n - divmod(n, p + 1)[1]
        self.xi = xi
        self.l = l
        AbstractDOE.__init__(self, n, p)
        self.sampleXNormalized = self._runDOE()

    def _runDOE(self):
        r = self.n // (self.p + 1)
        sampleXNormalized = self._screeningPlan(self.p, self.l, self.xi, r)
        return sampleXNormalized

    def _randorient(self, p, l, xi):
        """Generates a random orientation for a screening matrix

        :param p: number of design variables
        :param l: number of discrete levels along each dimension
        :param xi: elementary effect step length factor

        :return: Bstar - random orientation matrix
        """

        # Step length
        delta = xi / (l - 1.0)

        m = p + 1

        # A truncated p-level grid in one dimension
        xs = np.arange(0.0, 1 - delta + 1.0 / (l - 1), 1.0 / (l - 1))  # (0:1/(p-1):1-delta)
        xsl = len(xs)

        # Basic sampling matrix
        b = np.tril(np.ones((m, p)), -1)

        # Randomization
        # Matrix with +1s and -1s on the diagonal with equal probability
        # in Diss C*
        dStar = np.diag(np.round(np.random.uniform(size=p)) * 2 - 1)

        # Random base value
        xStar = (np.floor(np.random.uniform(size=p) * xsl)) / xsl

        # Permutation matrix; in Diss this is A*
        pStar = np.zeros((p, p))
        rp = np.random.permutation(p)
        for index in range(p):
            pStar[index, rp[index]] = 1.0

        # A random orientation of the sampling matrix
        bStar = np.dot(
            (
                np.dot(np.ones((m, 1)), np.array([xStar]))
                + (delta / 2.0) * (np.dot((2 * b - np.ones((m, p))), dStar) + np.ones((m, p)))
            ),
            pStar,
        )
        # (ones(m,1)*xstar+(Delta/2)*((2*B-ones(m,k))*Dstar+ones(m,k)))*Pstar;
        return bStar

    def _screeningPlan(self, p, l, xi, r):
        """Generates a Morris screening plan with a specified number of elementary effects for each variable.

        :param p: number of design variables
        :param l: number of discreet levels along each dimension
        :param xi: elementary effect step length factor
        :param r: number of random orientations (=number of elementary effects per variable).

        :return: screening plan with values of [0,1] of the shape (k+1*r, k)
        """
        retArray = self._randorient(p, l, xi)
        for index in range(r - 1):
            retArray = np.vstack((retArray, self._randorient(p, l, xi)))

        return retArray.T


class CentroidalVoronoiTesselation(AbstractDOE):
    """
    [1]Y. Saka, M. Gunzburger, and J. Burkardt, "Latinized, improved LHS, and CVT point sets in hypercubes," International Journal of Numerical Analysis and Modeling, vol. 4, no. 3–4, pp. 729–743, 2007.
    [2]L. Ju, Q. Du, and M. Gunzburger, "Probabilistic methods for centroidal Voronoi tessellations and their parallel implementations," Parallel Computing, vol. 28, no. 10, pp. 1477–1500, 2002.
    """

    doPlot = False

    def __init__(self, n, p, cellEstimatorCountFactor=5, maxIteration=1000, requiredStableRuns=10, initialDoe=None):
        """Also See AbstractDOE for documentation

        :param cellEstimatorCountFactor: The number of cell estimators can be calculated with this: n * cellEstimatorCountFactor.
            This value may be a float but greater zero.
        """
        self.doeGeneratorClass = MonteCarlo
        AbstractDOE.__init__(self, n, p)
        if cellEstimatorCountFactor <= 0:
            raise DelisMMError("cellEstimatorCountFactor is zero or negative")
        self.sampleXNormalized = self._runDOE(cellEstimatorCountFactor, maxIteration, requiredStableRuns, initialDoe)

    def _runDOE(self, cellEstimatorCountFactor, maxIteration, requiredStableRuns, initialDoe):
        """
        variables in [2]:

            z = generators
            q = cellEstimators
        """

        from scipy.spatial import cKDTree

        nCellEstimators = self.n * cellEstimatorCountFactor
        alpha, beta = (0.95, 0.05), (0.5, 0.5)
        if not alpha[1] >= 0 or not beta[1] >= 0 or not np.allclose([sum(alpha), sum(beta)], [1, 1]):
            raise DelisMMError("values of alpha and beta are malformed")

        # initial population
        if initialDoe is None:
            newGenerators = self.doeGeneratorClass(self.n, self.p).sampleXNormalized.T
        else:
            if initialDoe.n != self.n or initialDoe.p != self.p:
                raise DelisMMError("wrong doe parameters for initial doe")
            newGenerators = initialDoe.sampleXNormalized.T
        doeQuality0 = DOEQuality.mm(newGenerators.T)
        stable = 0
        best = None
        if self.doPlot:
            generatorsHistory = [newGenerators]
        log.info("cvt iterations start")
        cvtIteration = 0
        doeQuality = DOEQuality.mm(newGenerators.T)
        log.debug("CVT generation {}, quality of {}".format(cvtIteration, doeQuality))
        while 1:
            generators = newGenerators
            j = cvtIteration  # + 1
            c1, c2 = (alpha[0] * j + beta[0]) / (j + 1), (alpha[1] * j + beta[1]) / (j + 1)
            # create cell estimators
            cellEstimators = self.doeGeneratorClass(nCellEstimators, self.p).sampleXNormalized.T
            #             cellEstimators = MonteCarlo(nCellEstimators, self.p).sampleXNormalized.T

            # find nearest generators to each cell estimator
            tree = cKDTree(generators)
            _, nearestIndexes = tree.query(cellEstimators)

            # collect all cell estimators to each generator
            cellEstimatorDict = {}
            for nearestIndex, cellEstimator in zip(nearestIndexes, cellEstimators):
                if nearestIndex not in cellEstimatorDict:
                    cellEstimatorDict[nearestIndex] = []
                cellEstimatorDict[nearestIndex].append(cellEstimator)

            # calculate center(mean) of cell estimators for each voronoi cell
            cellCenters = generators.copy()

            for generatorIndex in cellEstimatorDict:
                cellCenter = np.mean(cellEstimatorDict[generatorIndex], axis=0)
                cellCenters[generatorIndex, :] = cellCenter
            newGenerators = c1 * generators + c2 * cellCenters
            cvtIteration += 1

            if self.doPlot:
                self._plotIteration(
                    generators, cellEstimators, nearestIndexes, newGenerators, cellCenters, cvtIteration
                )
                generatorsHistory.append(newGenerators)

            # ===================================================================
            # check quality and possibly converge
            # ===================================================================
            doeQuality = DOEQuality.mm(newGenerators.T)
            log.debug("CVT generation {}, quality of {}".format(cvtIteration, doeQuality))
            if doeQuality < doeQuality0:
                stable = 0
                best = generators
                doeQuality0 = doeQuality
            else:
                stable += 1
            if stable > requiredStableRuns and best is not None:
                log.info("Stable run at CVT generation {}, quality of {}".format(cvtIteration, doeQuality))
                break
            if cvtIteration >= maxIteration:
                log.info("MaxIteration reached with quality of {}".format(doeQuality))
                best = generators
                break

        doeQuality = DOEQuality.mm(newGenerators.T)

        if 1 and self.doPlot:
            self._plotIteration(generators, cellEstimators, nearestIndexes, newGenerators, cellCenters, cvtIteration)
            self._plotGeneratorTrace(generatorsHistory)
            import matplotlib.pyplot as plt

            plt.show()
        return best.T

    @staticmethod
    def _plotIteration(
        generators, cellEstimators, nearestIndexes=None, newGenerators=None, cellCenters=None, iteration=None
    ):
        """doc"""

        if generators.shape[1] != 2:
            log.info("not of dimension p=2")
            return
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(8, 6))
        ax = plt.gca()

        plt.scatter(cellEstimators.T[0], cellEstimators.T[1], s=20, c="b", alpha=0.5, label="cell estimators")
        plt.scatter(generators.T[0], generators.T[1], s=100, c="r", alpha=0.5, label="old generators")
        if newGenerators is not None:
            plt.scatter(newGenerators.T[0], newGenerators.T[1], s=100, c="g", alpha=0.5, label="new generators")
            for generator, newGenerator in zip(generators, newGenerators):
                ax.annotate(
                    "",
                    xy=newGenerator,
                    xycoords="data",
                    xytext=generator,
                    textcoords="data",
                    weight="bold",
                    color="g",
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3", color="g"),
                )
        if cellCenters is not None:
            plt.scatter(cellCenters.T[0], cellCenters.T[1], s=100, c="b", alpha=0.5, label="cell center")
            if nearestIndexes is not None:
                for estimator, generatorIndex in zip(cellEstimators, nearestIndexes):
                    cellCenter = cellCenters[generatorIndex]
                    plt.plot(*zip(estimator, cellCenter), c="black")
            if newGenerators is not None:
                for cellCenter, newGenerator in zip(cellCenters, newGenerators):
                    plt.plot(*zip(newGenerator, cellCenter), "g--")
        CentroidalVoronoiTesselation._setAxisLimits(ax)

        # shrink plot region by 20 percent
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

        # Put a legend to the right of the current axis
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

        print("generators")
        print(indent(generators, delim=" , "))
        print("newGenerators")
        print(indent(newGenerators, delim=" , "))
        print("cellEstimators")
        print(indent(cellEstimators, delim=" , "))
        print("cellCenters")
        print(indent(cellCenters, delim=" , "))
        print("nearestIndexes")
        print(indent([nearestIndexes], delim=" , "))

        fig.savefig("cvt_iteration_{}.png".format(iteration))

    def _plotGeneratorTrace(self, generatorsHistory):
        """doc"""
        if generatorsHistory and generatorsHistory[0].shape[1] != 2:
            log.info("not of dimension p=2")
            return
        import matplotlib.pyplot as plt

        plt.figure()

        lastGenerators = generatorsHistory[0]
        for generators, transparency in zip(generatorsHistory[1:], np.linspace(0, 0.7, len(generatorsHistory) - 1)):
            for generator, lastGenerator in zip(lastGenerators, generators):
                plt.plot(*zip(generator, lastGenerator), c="black", alpha=transparency)
            # plt.plot(*zip(lastGenerators, generators), c = 'black', alpha=transparency)
            # plt.scatter(generators.T[0], generators.T[1], s=10, c='r', alpha=transparency)
            lastGenerators = generators
        plt.scatter(generatorsHistory[-1].T[0], generatorsHistory[-1].T[1], s=100, c="r", alpha=1)
        self._setAxisLimits(plt.gca())

    @staticmethod
    def _setAxisLimits(ax):
        """doc"""
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)


class LatinizedCentroidalVoronoiTesselation(CentroidalVoronoiTesselation):
    """Latinized version of CVT

    For latinization see chapter 4 in
    [1] Y. Saka, M. Gunzburger, and J. Burkardt, "Latinized, improved LHS, and CVT point sets in hypercubes," International Journal of Numerical Analysis and Modeling, vol. 4, no. 3–4, pp. 729–743, 2007.
    """

    def __init__(self, *args, **kwargs):
        """Also See AbstractDOE for documentation"""
        CentroidalVoronoiTesselation.__init__(self, *args, **kwargs)
        samples = self.sampleXNormalized
        self.sampleXNormalized = self.latinizeSampleXNormalized(self.sampleXNormalized)
        doeQuality = DOEQuality.mm(self.sampleXNormalized)
        log.info("LCVT quality of {}".format(doeQuality))

        if self.doPlot:
            self._plotLatinization(samples, self.sampleXNormalized)

    def _plotLatinization(self, sampleXBefore, sampleXAfter):
        """doc"""
        if sampleXBefore.shape[0] != 2:
            log.info("not of dimension p=2")
            return

        import matplotlib.pyplot as plt

        plt.figure()
        plt.scatter(sampleXBefore.T[:, 0], sampleXBefore.T[:, 1], s=100, c="r", alpha=1)
        plt.scatter(sampleXAfter.T[:, 0], sampleXAfter.T[:, 1], s=100, c="b", alpha=1)
        self._setAxisLimits(plt.gca())
        plt.show()


class ScaledCentroidalVoronoiTesselation(CentroidalVoronoiTesselation):
    """The CVT values are inside the unit cube. The samples are scaled to [0,1]"""

    def __init__(self, *args, **kwargs):
        """Also See AbstractDOE for documentation"""
        CentroidalVoronoiTesselation.__init__(self, *args, **kwargs)
        self.scaleSamples()

    def scaleSamples(self):
        """doc"""

        newSamples = []
        samples = self.sampleXNormalized
        for paramSamples in samples:
            minVal, maxVal = np.min(paramSamples), np.max(paramSamples)
            paramSamples = (paramSamples - minVal) / (maxVal - minVal)
            newSamples.append(paramSamples)

        newSamples = np.array(newSamples)
        self.sampleXNormalized = newSamples

        doeQuality = DOEQuality.mm(self.sampleXNormalized)
        log.info("SCVT quality of {}".format(doeQuality))

        if self.doPlot:
            self._plotLatinization(samples, self.sampleXNormalized)

    def _plotSampleSets(self, sampleXBefore, sampleXAfter):
        """doc"""
        if sampleXBefore.shape[0] != 2:
            log.info("not of dimension p=2")
            return

        import matplotlib.pyplot as plt

        plt.figure()
        plt.scatter(sampleXBefore.T[:, 0], sampleXBefore.T[:, 1], s=100, c="r", alpha=1)
        plt.scatter(sampleXAfter.T[:, 0], sampleXAfter.T[:, 1], s=100, c="b", alpha=1)
        self._setAxisLimits(plt.gca())
        plt.show()


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    if 0:
        doe = ScaledCentroidalVoronoiTesselation(20, 2)
        initialSamples = doe.sampleXNormalized
        doe.scaleSamples()
        doe._plotSampleSets(initialSamples, doe.sampleXNormalized)
    elif 0:
        doe = LatinHypercube(5, 2)
        print(indent(doe.sampleXNormalized, delim=", "))
    elif 1:
        log.logLevel = 10
        CentroidalVoronoiTesselation.doPlot = True
        doe = CentroidalVoronoiTesselation(
            9, 2, requiredStableRuns=100
        )  # , maxIteration = 300, cellEstimatorCountFactor = 10)

        samples = np.array([np.linspace(0, 1, 100), np.linspace(0, 1, 100)])
        print(samples)
        print(DOEQuality.mm(samples))
    elif 1:
        generators = np.array(
            [
                [0.76629408533, 0.166305226647],
                [0.293062940846, 0.681128562962],
                [0.726354951027, 0.788534292217],
                [0.402460538682, 0.0923247590001],
            ]
        )
        newGenerators = [
            [0.756860179899, 0.239727887205],
            [0.281123104862, 0.732778252933],
            [0.726354951027, 0.788534292217],
            [0.378261243462, 0.134339794939],
        ]
        cellEstimators = [
            [0.492972608182, 0.374410925403],
            [0.397927746531, 0.274669721494],
            [0.731988974671, 0.433296719586],
            [0.065332619838, 0.207614376813],
            [0.513328621031, 0.104124972234],
            [0.390262761025, 0.864705490092],
            [0.109027949879, 0.873185744714],
            [0.102753912002, 0.264713543399],
        ]
        cellCenters = [
            [0.731988974671, 0.433296719586],
            [0.249645355452, 0.868945617403],
            [0.726354951027, 0.788534292217],
            [0.314463101517, 0.245106707869],
        ]
        nearestIndexes = [3, 3, 0, 3, 3, 1, 1, 3]

        CentroidalVoronoiTesselation._plotIteration(
            np.array(generators),
            np.array(cellEstimators),
            np.array(nearestIndexes),
            np.array(newGenerators),
            np.array(cellCenters),
        )
        plt.show()
