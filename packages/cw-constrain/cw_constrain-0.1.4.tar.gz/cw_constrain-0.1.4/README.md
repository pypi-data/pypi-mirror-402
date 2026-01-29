# cw_constrain

[![PyPI version](https://badge.fury.io/py/cw-constrain.svg)](https://pypi.org/project/cw-constrain/)
[![DOI](https://zenodo.org/badge/993593119.svg)](https://doi.org/10.5281/zenodo.15559327)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

`cw_constrain` is a Python package designed to provide tools and methods for constraining PBH abundance and the MSP hypothesis for the GeV excess using upper limits derived from continuous gravitational wave searches on real LIGO-Virgo-KAGRA data. It includes modules for analyzing GeV excess constraints, primordial black hole constraints, and shared utilities.

---

## Features

- Calculate constraints on MSP luminosity functions that explain the GeV excess using your own luminosity function, your own rotational frequency distribution and/or your own ellipticity distribution.
- Compute constraints on the fraction of dark matter that primordial black hole (PBHs) could compose using your own mass function or PBH formation model.
- Utility functions shared across modules for data processing
- Well-structured package suitable for scientific research and data analysis

---

## GeV excess constraints: how to use your own luminosity function

Please follow the tutorial in `tutorials/O4a_GeV_excess_tutorial.ipynb`

---

## Constraining PBH abundance with your own mass functions or formation models 

### PBH asteroid-mass constraints:


Please follow the tutorial in `tutorials/O4a_pbh_all_sky_tutorial.ipynb`

---

### PBH planetary-mass constraints:


Please follow the tutorial in `tutorials/O4a_light_pbh_tutorial.ipynb`

---

### Ultralight dark-matter constraints

Please follow the tutorial in `tutorials/O4a_DM_interaction_tutorial.ipynb`


## Installation

You can install the package directly from PyPI:

```bash
pip install cw-constrain
```

And then in Python:

`import cw_constrain`


If you use these codes, please cite the following Zenodo release:

[![DOI](https://zenodo.org/badge/993593119.svg)](https://doi.org/10.5281/zenodo.15559327)

as well as the original papers:

Constraining the millisecond pulsar hypothesis for the GeV excess

```
@article{Miller:2023qph,
    author = "Miller, Andrew L. and Zhao, Yue",
    title = "{Probing the Pulsar Explanation of the Galactic-Center GeV Excess Using Continuous Gravitational-Wave Searches}",
    eprint = "2301.10239",
    archivePrefix = "arXiv",
    primaryClass = "astro-ph.HE",
    doi = "10.1103/PhysRevLett.131.081401",
    journal = "Phys. Rev. Lett.",
    volume = "131",
    number = "8",
    pages = "081401",
    year = "2023"
}
```

Constraing asteroid-mass PBH abundance

```
@article{Miller:2021knj,
    author = "Miller, Andrew L. and Aggarwal, Nancy and Clesse, S\'ebastien and De Lillo, Federico",
    title = "{Constraints on planetary and asteroid-mass primordial black holes from continuous gravitational-wave searches}",
    eprint = "2110.06188",
    archivePrefix = "arXiv",
    primaryClass = "gr-qc",
    doi = "10.1103/PhysRevD.105.062008",
    journal = "Phys. Rev. D",
    volume = "105",
    number = "6",
    pages = "062008",
    year = "2022"
}
```

Constraining planetary-mass PBH abundance:

```
@article{Miller:2024fpo,
    author = "Miller, Andrew L. and Aggarwal, Nancy and Clesse, S\'ebastien and De Lillo, Federico and Sachdev, Surabhi and Astone, Pia and Palomba, Cristiano and Piccinni, Ornella J. and Pierini, Lorenzo",
    title = "{Gravitational Wave Constraints on Planetary-Mass Primordial Black Holes Using LIGO O3a Data}",
    eprint = "2402.19468",
    archivePrefix = "arXiv",
    primaryClass = "gr-qc",
    doi = "10.1103/PhysRevLett.133.111401",
    journal = "Phys. Rev. Lett.",
    volume = "133",
    number = "11",
    pages = "111401",
    year = "2024"
}

@article{Miller:2024jpo,
    author = "Miller, Andrew L. and Aggarwal, Nancy and Clesse, Sebastien and De Lillo, Federico and Sachdev, Surabhi and Astone, Pia and Palomba, Cristiano and Piccinni, Ornella J. and Pierini, Lorenzo",
    title = "{Method to search for inspiraling planetary-mass ultracompact binaries using the generalized frequency-Hough transform in LIGO O3a data}",
    eprint = "2407.17052",
    archivePrefix = "arXiv",
    primaryClass = "astro-ph.IM",
    doi = "10.1103/PhysRevD.110.082004",
    journal = "Phys. Rev. D",
    volume = "110",
    number = "8",
    pages = "082004",
    year = "2024"
}
```
