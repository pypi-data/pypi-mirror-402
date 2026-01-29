import os

import numpy as np
from patme.service.logger import log

from delismm.control.tank import getKrigings
from delismm.model.metrics import relativeRootMeanSquareError, rootMeanSquareError


def main():

    baseDir = f"C:\\Users\\jaco_li\\Tools\\delismm\\tmp\\tank_surrogates_20250801_175648\\"
    runDir = surrogatesDir = os.path.join(baseDir, "by_diameter_length")
    results = [("totalMass_in_kg", 4, False), ("volume_in_l", 5, False), ("cylinderThickness_in_mm", 10, False)]
    parameters = ["diameter", "length", "pressure", "helicalDesignFactor"]
    mms = getKrigings(runDir, surrogatesDir, parameters, results)
    # accuracy
    for mm in mms:
        crossSampleY = mm.getCrossValidationValues()
        sample1, sample2 = (
            (np.power(10, mm.sampleY), np.power(10, crossSampleY)) if mm.log10SampleY else (mm.sampleY, crossSampleY)
        )
        rmse = rootMeanSquareError(sample1, sample2)
        rmsre = relativeRootMeanSquareError(sample1, sample2)
        log.info(f"\nRMSE: {rmse}\nRMSRE: {rmsre}")

    runDir = surrogatesDir = os.path.join(baseDir, "by_diameter_volume")
    results = [("totalMass_in_kg", 4, False), ("length_in_mm", 8, False), ("cylinderThickness_in_mm", 10, False)]
    parameters = ["diameter", "volume", "pressure", "helicalDesignFactor"]
    mms = getKrigings(runDir, surrogatesDir, parameters, results)
    # accuracy
    for mm in mms:
        crossSampleY = mm.getCrossValidationValues()
        sample1, sample2 = (
            (np.power(10, mm.sampleY), np.power(10, crossSampleY)) if mm.log10SampleY else (mm.sampleY, crossSampleY)
        )
        rmse = rootMeanSquareError(sample1, sample2)
        rmsre = relativeRootMeanSquareError(sample1, sample2)
        log.info(f"\nRMSE: {rmse}\nRMSRE: {rmsre}")

    runDir = surrogatesDir = os.path.join(baseDir, "by_length_volume")
    results = [
        ("dcyl_in_mm", 5, False),
    ]
    parameters = ["length", "volume", "pressure", "helicalDesignFactor"]
    mms = getKrigings(runDir, surrogatesDir, parameters, results)
    # accuracy
    for mm in mms:
        crossSampleY = mm.getCrossValidationValues()
        sample1, sample2 = (
            (np.power(10, mm.sampleY), np.power(10, crossSampleY)) if mm.log10SampleY else (mm.sampleY, crossSampleY)
        )
        rmse = rootMeanSquareError(sample1, sample2)
        rmsre = relativeRootMeanSquareError(sample1, sample2)
        log.info(f"\nRMSE: {rmse}\nRMSRE: {rmsre}")


if __name__ == "__main__":
    main()
