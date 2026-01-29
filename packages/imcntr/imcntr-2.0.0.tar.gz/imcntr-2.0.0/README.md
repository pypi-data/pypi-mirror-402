# imcntr

A package providing an API for imaging controller based on an Arduino Nano Every to communicate via serial port.

## Installation

```bash
$ pip install imcntr
```



## Description

This package was developed to communicate with the controller of the neutron imaging experiment at TRIGA Mark II at Atominstitut of TU Wien. `imcntr` provides an API to access controller functionality via Python scripts. Communication is done via a serial port. The controller, and thus the package, can be used in general for imaging experiments with radiation. The controller provides a set of functions, such as moving the sample in and out of the beam, rotating the sample for tomographic experiments, and opening and closing the beam shutter. It provides an API to access controller functionality via Python scripts.

## Usage

```{literalinclude} ../examples/basic_usage.py
:language: python
:linenos:
```

## Contributing

Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a Code of Conduct. By contributing to this project, you agree to abide by its terms.

## License

`imcntr` was created by Clemens Trunner. It is licensed under the terms of the MIT license.

## Credits

`imcntr` was created with [`cookiecutter`](https://cookiecutter.readthedocs.io/en/latest/) and the `py-pkgs-cookiecutter` [template](https://github.com/py-pkgs/py-pkgs-cookiecutter).
