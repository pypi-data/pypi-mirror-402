# delismm

Delismm is a pure python package for the creation of kriging-based metamodels.

It covers the following features:

- Perform parameter sensitivity analysis
- Generate Design of Experiments (DOE)
- Save/Load DOE
- Create Kriging Metamodels
- Create hierarchical kriging metamodels
- Perform a resampling to generate new Designs and improve the model
- Run DOEs using various parallelization methods local and remote


## Installation and Usage

At least you require Python >= 3.9 to run delismm. To install it, extract the archive and perform the following steps:


```
cd delismm
python setup.py install
```


A simple example:

```
from delismm.example import runExample
runExample()
```

This will create a

- doe
- sample values
- kriging model
- a diagram


## Contributing to _delismm_

We welcome your contribution!

If you want to provide a code change, please:

* Create a fork of the GitLab project.
* Develop the feature/patch
* Provide a merge request.

> If it is the first time that you contribute, please add yourself to the list
> of contributors below.


## Citing

If you use this work in a scientific publication, please cite the specific version that you used as follows:

> Sebastian Freund : "delismm", <RELEASE_NUMBER>, <Publication_Date>, <Git_Repository_URL>

You can find information about the release number and the publication date in the [changelog](changelog.md).


## License

MIT

## Change Log

see [changelog](changelog.md)

## Authors

[Sebastian Freund](mailto:sebastian.freund@dlr.de)
