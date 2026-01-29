# Copyright (C) 2013 Deutsches Zentrum fuer Luft- und Raumfahrt(DLR, German Aerospace Center) <www.dlr.de>
"""
Delismm is a pure python package for the creation of kriging-based metamodels.

It covers the following features:

- Perform parameter sensitivity analysis
- Generate Design of Experiments (DOE)
- Save/Load DOE
- Create Kriging Metamodels
- Create hierarchical kriging metamodels
- Perform a resampling to generate new Designs and improve the model
- Run DOEs using various parallelization methods local and remote


A simple example:

   >>> from delismm.example import runExample
   >>> runExample(doPlot = False)

This will create a

- doe
- sample values
- kriging model
- a diagram (if doPlot is active)


"""

from importlib import metadata
from pathlib import Path

from patme import getPyprojectMeta

name = Path(__file__).parent.name

try:
    # if full git repo is present, read pyproject.toml
    pkgMeta = getPyprojectMeta(__file__)
    version = str(pkgMeta["version"])
    programDir = str(Path(__file__).parents[2])
    description = str(pkgMeta["description"])
except FileNotFoundError:
    try:
        # package is installed
        version = metadata.version(name)
        programDir = str(Path(__file__).parent)
        description = metadata.version(name)
    except metadata.PackageNotFoundError:
        # We have only the source code or somehow the package is corrupt
        version = str("version not provided")
        programDir = str(Path(__file__).parent)
        description = ""
