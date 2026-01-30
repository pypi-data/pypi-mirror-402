# adnus (AdNuS):  Advanced Number Systems.

---
[![PyPI version](https://badge.fury.io/py/adnus.svg)](https://badge.fury.io/py/adnus)

[![License: MIT](https://img.shields.io/badge/License-AGPL-yellow.svg)](https://opensource.org/license/agpl-v3)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16341919.svg)](https://doi.org/10.5281/zenodo.16341919)

[![WorkflowHub DOI](https://img.shields.io/badge/DOI-10.48546/workflowhub.datafile.23.1-blue)](https://doi.org/10.48546/workflowhub.datafile.23.1)

[![figshare DOI](https://img.shields.io/badge/DOI-10.6084/m9.figshare.29621336-blue)](https://doi.org/10.6084/m9.figshare.29621336)

[![OSF DOI](https://img.shields.io/badge/DOI-10.17605/OSF.IO/9C26Y-blue)](https://doi.org/10.17605/OSF.IO/9C26Y)

[![Anaconda-Server Badge](https://anaconda.org/bilgi/adnus/badges/version.svg)](https://anaconda.org/bilgi/adnus)
[![Anaconda-Server Badge](https://anaconda.org/bilgi/adnus/badges/latest_release_date.svg)](https://anaconda.org/bilgi/adnus)
[![Anaconda-Server Badge](https://anaconda.org/bilgi/adnus/badges/platforms.svg)](https://anaconda.org/bilgi/adnus)
[![Anaconda-Server Badge](https://anaconda.org/bilgi/adnus/badges/license.svg)](https://anaconda.org/bilgi/adnus)

[![Open Source](https://img.shields.io/badge/Open%20Source-Open%20Source-brightgreen.svg)](https://opensource.org/)
[![Documentation Status](https://app.readthedocs.org/projects/adnus/badge/?0.1.0=main)](https://adnus.readthedocs.io/en/latest)

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/-/badge)](https://www.bestpractices.dev/projects/-)

[![Python CI](https://github.com/WhiteSymmetry/adnus/actions/workflows/python_ci.yml/badge.svg?branch=main)](https://github.com/WhiteSymmetry/adnus/actions/workflows/python_ci.yml)
[![codecov](https://codecov.io/gh/WhiteSymmetry/adnus/graph/badge.svg?token=ES98M5WZFI)](https://codecov.io/gh/WhiteSymmetry/adnus)
[![Documentation Status](https://readthedocs.org/projects/adnus/badge/?version=latest)](https://adnus.readthedocs.io/en/latest/)
[![Binder](https://terrarium.evidencepub.io/badge_logo.svg)](https://terrarium.evidencepub.io/v2/gh/WhiteSymmetry/adnus/HEAD)
[![PyPI version](https://badge.fury.io/py/adnus.svg)](https://badge.fury.io/py/adnus)
[![PyPI Downloads](https://static.pepy.tech/badge/adnus)](https://pepy.tech/projects/adnus)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)
[![Linted with Ruff](https://img.shields.io/badge/Linted%20with-Ruff-green?logo=python&logoColor=white)](https://github.com/astral-sh/ruff)

---

<p align="left">
    <table>
        <tr>
            <td style="text-align: center;">PyPI</td>
            <td style="text-align: center;">
                <a href="https://pypi.org/project/adnus/">
                    <img src="https://badge.fury.io/py/adnus.svg" alt="PyPI version" height="18"/>
                </a>
            </td>
        </tr>
        <tr>
            <td style="text-align: center;">Conda</td>
            <td style="text-align: center;">
                <a href="https://anaconda.org/bilgi/adnus">
                    <img src="https://anaconda.org/bilgi/adnus/badges/version.svg" alt="conda-forge version" height="18"/>
                </a>
            </td>
        </tr>
        <tr>
            <td style="text-align: center;">DOI</td>
            <td style="text-align: center;">
                <a href="https://doi.org/10.5281/zenodo.16341919">
                    <img src="https://zenodo.org/badge/DOI/10.5281/zenodo.16341919.svg" alt="DOI" height="18"/>
                </a>
            </td>
        </tr>
        <tr>
            <td style="text-align: center;">License: AGPL</td>
            <td style="text-align: center;">
                <a href="https://opensource.org/license/agpl-v3">
                    <img src="https://img.shields.io/badge/License-AGPL-yellow.svg" alt="License" height="18"/>
                </a>
            </td>
        </tr>
    </table>
</p>

---
# adnus (AdNuS):  Advanced Number Systems.

`adnus` is a Python library that provides an implementation of various advanced number systems. This library is designed for mathematicians, researchers, and developers who need to work with number systems beyond the standard real and complex numbers.

## Features

- **Harmonic and Oresme Sequences**: Functions to generate harmonic numbers and Oresme sequences.
- **Bicomplex Numbers**: A class for bicomplex numbers with full arithmetic support.
- **Neutrosophic Numbers**: Classes for neutrosophic numbers, including their complex and bicomplex extensions.
- **Hyperreal Numbers**: A conceptual implementation of hyperreal numbers.
- **Extensible Design**: Built with an abstract base class to easily extend and add new number systems.
- **Fully Typed**: The library is fully type-hinted for better code quality and maintainability.
- **Real numbers**
- **Complex numbers**
- **Quaternion numbers**
- **Octonion numbers**
- **Sedenion numbers**
- **Pathion numbers**
- **Chingon numbers**
- **Routon numbers**
- **Voudon  numbers**

## Installation

To install the library, clone the repository and use Poetry:

```bash
git clone https://github.com/WhiteSymmetry/adnus.git
cd adnus
poetry install
```

## Kullanım (Türkçe) / Usage (English)

Here's a quick overview of how to use the different number systems available in `adnus`.

### Bicomplex Numbers

```python
import adnus as ad
#from adnus import BicomplexNumber

z1 = ad.BicomplexNumber(1 + 2j, 3 + 4j)
z2 = ad.BicomplexNumber(5 + 6j, 7 + 8j)

print(f"Addition: {z1 + z2}")
print(f"Multiplication: {z1 * z2}")
```

### Neutrosophic Numbers

```python
import adnus as ad
# from adnus import NeutrosophicNumber

n1 = ad.NeutrosophicNumber(1.5, 2.5)
n2 = ad. NeutrosophicNumber(3.0, 4.0)

print(f"Addition: {n1 + n2}")
print(f"Multiplication: {n1 * n2}")
```

```python
import adnus as ad
# Complex(0, 0) bir HypercomplexNumber örneği döndürür
ComplexClass = type(ad.Complex(0, 0))
C = ad.cayley_dickson_process(ComplexClass)
print(C(3-7j))
```

```python
import adnus as ad 
q1 = ad.Quaternion(1, 2, 3, 4)
q2 = ad.Quaternion(5, 6, 7, 8)
print(f"Quaternions: {q1} * {q2} = {q1 * q2}")
```

## Running Tests

To ensure everything is working correctly, you can run the included tests using `pytest`:

```bash
poetry run pytest
```

---

## Kurulum (Türkçe) / Installation (English)

### Python ile Kurulum / Install with pip, conda, mamba
```bash
pip install adnus -U
python -m pip install -U adnus
conda install bilgi::adnus -y
mamba install bilgi::adnus -y
```

```diff
- pip uninstall adnus -y
+ pip install -U adnus
+ python -m pip install -U adnus
```

[PyPI](https://pypi.org/project/adnus/)

### Test Kurulumu / Test Installation

```bash
pip install -i https://test.pypi.org/simple/ adnus -U
```

### Github Master Kurulumu / GitHub Master Installation

**Terminal:**

```bash
pip install git+https://github.com/WhiteSymmetry/adnus.git
```

**Jupyter Lab, Notebook, Visual Studio Code:**

```python
!pip install git+https://github.com/WhiteSymmetry/adnus.git
# or
%pip install git+https://github.com/WhiteSymmetry/adnus.git
```

---

### Development
```bash
# Clone the repository
git clone https://github.com/WhiteSymmetry/adnus.git
cd adnus

# Install in development mode
python -m pip install -ve . # Install package in development mode

# Run tests
pytest

Notebook, Jupyterlab, Colab, Visual Studio Code
!python -m pip install git+https://github.com/WhiteSymmetry/adnus.git
```
---

## Citation

If this library was useful to you in your research, please cite us. Following the [GitHub citation standards](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/creating-a-repository-on-github/about-citation-files), here is the recommended citation.

### BibTeX


### APA

```

Keçeci, M. (2025). adnus [Data set]. ResearchGate. https://doi.org/

Keçeci, M. (2025). adnus [Data set]. OSF. https://doi.org/10.17605/OSF.IO/9C26Y

Keçeci, M. (2025). adnus [Data set]. figshare. https://doi.org/10.6084/m9.figshare.29621336

Keçeci, M. (2025). adnus [Data set]. WorkflowHub. https://doi.org/10.48546/workflowhub.datafile.23.1

Keçeci, M. (2025). adnus. Open Science Articles (OSAs), Zenodo. https://doi.org/10.5281/zenodo.16341919

```

### Chicago

```


Keçeci, Mehmet. adnus [Data set]. ResearchGate, 2025. https://doi.org/

Keçeci, M. (2025). adnus [Data set]. figshare. https://doi.org/10.6084/m9.figshare.29621336

Keçeci, Mehmet. adnus [Data set]. WorkflowHub, 2025. https://doi.org/10.48546/workflowhub.datafile.23.1

Keçeci, Mehmet. adnus. Open Science Articles (OSAs), Zenodo, 2025. https://doi.org/10.5281/zenodo.16341919

```


### Lisans (Türkçe) / License (English)

```
This project is licensed under the AGPL License.
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any bugs or feature requests.

# Pixi:

[![Pixi](https://img.shields.io/badge/Pixi-Pixi-brightgreen.svg)](https://prefix.dev/channels/bilgi)

pixi init adnus

cd adnus

pixi workspace channel add https://repo.prefix.dev/bilgi --prepend

✔ Added https://repo.prefix.dev/bilgi

pixi add adnus

✔ Added adnus >=0.2.0,<2

pixi install

pixi shell

pixi run python -c "import adnus; print(adnus.__version__)"

### Çıktı: 0.2.0

pixi remove adnus

conda install -c https://prefix.dev/bilgi adnus

pixi run python -c "import adnus; print(adnus.__version__)"

### Çıktı: 0.2.0

pixi run pip list | grep adnus

### adnus  0.2.0

pixi run pip show adnus

Name: adnus

Version: 0.2.0

Summary: A Python library for Advanced Number Systems (AdNuS), including Bicomplex, Neutrosophic, Hyperreal numbers, reals, Complex, Quaternion, Octonion, Sedenion, Pathion, Chingon, Routon, Voudon.

Home-page: https://github.com/WhiteSymmetry/adnus

Author: Mehmet Keçeci

Author-email: Mehmet Keçeci <...>

License: GNU AFFERO GENERAL PUBLIC LICENSE

Copyright (c) 2025-2026 Mehmet Keçeci
