# quantum-learn

[![PyPI Version](https://img.shields.io/pypi/v/quantum-learn.svg)](https://pypi.org/project/quantum-learn/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/OsamaMIT/quantum-learn/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/quantum-learn.svg)](https://pypi.org/project/quantum-learn/)

**quantum-learn** is an open-source Python library that simplifies **Quantum Machine Learning (QML)** using **PennyLane**.

Inspired by **scikit-learn** and **fastai**, it provides a high-level interface that abstracts both ***hybrid*** _and_ ***pure*** quantum machine learning.

## Features

- **Simple setup** that abstracts the process of training quantum models 
- Supports both hybrid quantum and pure quantum machine learning:
    - **Pure:** Variational Quantum Circuits (VQC)
    - **Hybrid:** (*Generalized*) Classification, Clustering, Regression
- Works with **PennyLane**, **scikit-learn**, and standard ML tools
- Can be run on any simulated or real quantum hardware supported by Pennylane (includes the majority of industry standards)

## Installation

quantum-learn requires **Python 3.6+**. Install it via pip:

```bash
pip install quantum-learn
```

Or install from source:

```bash
git clone https://github.com/OsamaMIT/quantum-learn.git
cd quantum-learn
pip install .
```

## Documentation
For tutorials, examples, and details on the classes, check out the [quantum-learn documentation](https://quantum-learn.readthedocs.io/en/latest/).

## Dependencies
The required dependencies can be installed by

```bash
pip install -r requirements.txt
```

## Planned Features
- Implement quantum kernel methods
- Implement categorical feature maps

## Contributing
Contributions are welcome! To contribute:

1. Fork the repository
2. Create a new branch (feature-branch)
3. Commit your changes and open a pull request

## License
This project is licensed under the MIT License. See the LICENSE file for details.
