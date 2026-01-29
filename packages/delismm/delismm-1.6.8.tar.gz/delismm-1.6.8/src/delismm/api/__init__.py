# -*- coding: utf-8 -*-
"""
api functions for delismm
"""

import errno
import os
from argparse import ArgumentParser
from collections import OrderedDict
from typing import List

import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from patme import epsilon

from delismm import description, name, programDir, version
from delismm.model.surrogate import AbstractSurrogate

modelDir = os.path.join(programDir, "models")
loadedSurrogates = {}

# instantiate the api
app = FastAPI(title=name, description=description, version=version, docs_url="/documentation")


@app.get("/")
def read_root() -> dict:
    """
    This function points to the main root of the api

    Returns
    -------
    dict
        Hello World
    """
    return {"HelloWorld": "please call the endpoint /documentation to obtain an api documentation"}


@app.get("/list_surrogates")
def list_surrogates() -> dict:
    """
    Lists all surrogates present in the surrogate folder

    Returns
    -------
    dict
        Maps an incemented index to the surrogate name
    """

    surrogateNames = getSurrogateNames()
    surrogates = [(surrogateIndex, surrogateName) for surrogateIndex, surrogateName in enumerate(surrogateNames)]
    surrogateDict = OrderedDict(surrogates)
    return surrogateDict


@app.get("/surrogate_info/{surrogate_name}")
def surrogate_info(surrogate_name: str) -> dict:
    """
    Lists all surrogates present in the surrogate folder

    Parameters
    ----------
    - surrogate_name : string, name of the surrogate as returned from "list_surrogates"

    Raises
    ------
    HTTPException if the given surrogate_name does not exist

    Returns
    -------
    :return: dict
        Maps surrogate properites to their values
    """
    surrogate = getSurrogate(surrogate_name)
    info = surrogate.getKrigingDocumentationDict()
    return info.model_dump()


@app.get("/call/")
def call(surrogate_name: str = Query(None), parameters: List[float] = Query(None), boundsError: bool = Query(False)):
    """
    Calls a surrogate with its parameters

    Parameters
    ----------
    - surrogate_name : list with model parameters
    - parameters : list of parameters of the surrogate model
    - boundsError : bool, optional. Raises HTTPException if a parameter is out of bounds

    Raises
    ------
    HTTPException when
    - the given surrogate_name does not exist
    - when the number of given parameters does not match the surrogates number of parameters
    - the parameters are out of bounds and boundsError == True

    Returns
    -------
    dict
        surrogate result
    """
    surrogate = getSurrogate(surrogate_name)
    if len(parameters) != surrogate.p:
        raise HTTPException(
            status_code=404,
            detail=f"number of parameters do not match! "
            f"Surrogate uses {surrogate.p} parameters but got {len(parameters)}",
        )
    if boundsError:
        normalizedParameters = surrogate.getParametersNormalized(parameters)
        paramOutOfBounds = (normalizedParameters < -epsilon) | (normalizedParameters > 1 + epsilon)
        if any(paramOutOfBounds):
            boundsInfoList = [
                f"{lb} <= {p} <= {ub}" for lb, ub, p in zip(surrogate.lowerBounds, surrogate.upperBounds, parameters)
            ]
            raise HTTPException(
                status_code=404,
                detail=f"Parameter bounds error: {list(zip(surrogate.parameterNames, paramOutOfBounds, boundsInfoList))}",
            )
    res = surrogate(parameters)[0]
    return res


def getSurrogateNames():
    """returns a list of valid surrogate names"""
    return sorted(
        os.path.splitext(filename)[0] for filename in os.listdir(modelDir) if os.path.splitext(filename)[1] == ".pickle"
    )


def getSurrogate(surrogate_name):
    """returns the surrogate with the given name"""
    if surrogate_name in loadedSurrogates:
        return loadedSurrogates[surrogate_name]
    if surrogate_name not in getSurrogateNames():
        raise HTTPException(status_code=404, detail=f'no such surrogate: "{surrogate_name}"')
    surrogate = AbstractSurrogate.load(os.path.join(modelDir, surrogate_name + ".pickle"))
    loadedSurrogates[surrogate_name] = surrogate
    return surrogate


if __name__ == "__main__":
    ap = ArgumentParser(description="Starts app to calculate tank metamodel results")
    ap.print_usage = ap.print_help  # redirecting the print_usage method to the extended print_help method
    ap.add_argument("-d", "--dir", dest="dir", help="Relative Path to the actual directory", metavar="DIR")
    ap.add_argument("-p", "--port", dest="port", type=int, default=8000, help="Port of the web server")
    options = ap.parse_args()
    if options.dir:
        modelDir = os.path.join(programDir, options.dir)
        if not os.path.exists(modelDir):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), modelDir)
    uvicorn.run(app, host="0.0.0.0", port=options.port)
