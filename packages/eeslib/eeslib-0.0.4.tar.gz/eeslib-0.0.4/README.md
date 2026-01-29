# EESLib

EESLib is a Python library for heat transfer and thermodynamics calculations, derived from Engineering Equation Solver (EES) functions. It is designed for educational use in the ME564 Heat Transfer course at the University of Wisconsin-Madison.

## Features

EESLib provides implementations for various engineering calculations including:

### Fluid Properties
- Thermodynamic properties (enthalpy, entropy, density, etc.) using CoolProp
- Functions for common fluids with temperature, pressure, and quality inputs
- NOTE: The CoolProp fluid property implementation approach differs from the fluid properties in EES! Do not expect perfect correspondence between properties obtained using either method. CoolProp is generally less robust and slower than the native EES implementation.

### Heat Transfer Functions
- **Internal Flow**: Nusselt number and friction factor calculations for pipe and duct flow (laminar, turbulent, transitional)
- **External Flow**: Heat transfer and friction for flow over plates, cylinders, and other geometries
- **Boiling and Condensation**: Heat transfer correlations for boiling and condensing fluid with various geometries
- **Heat Exchangers**: NTU and LMTD calculations for various flow configurations
- **Fin Efficiency**: Efficiency calculations for fins with various profiles and tip boundary conditions
- **Radiation**: Blackbody radiation, view factors, and radiative heat transfer functions. Note that a catalog of view factors with number ID assignments is provided in a PDF distributed in the source code folder.

### Utilities
- Unit conversions 
- Lookup tables for various properties
- Talbot inversion for Laplace transforms
- Result printing and PDF generation utilities

## Installation

### Prerequisites
- Python 3.14 or higher
- Packages listed in `requirements.txt`

### Install from PyPi

#### Quick Setup

Open a command window with the same privileges used to install Python. 
```bash
conda activate me564 
pip install eeslib
```

#### Full Setup
1.	Download miniconda executable from (https://www.anaconda.com/download/success#miniconda)  
2.	Run installer:
    * Choose "Just for me" option
    * Check 'yes' for Add Miniconda3 to PATH, and 'yes' for registering as the default Python
3.	Download code resources from Canvas: Files/Lectures/examples_<version#>.zip. 
This folder contains a number of examples that we’ll use in both lecture and homework codes. 
4.	Create the me564 environment in conda. In the command window, type:
    ```
    conda create -n me564 python=3.14
    ```
5.	Open command window (shell). Navigate your command window to the folder you downloaded. For example, type: 
    ```
    cd C:/path/to/my/folder/examples
    ```
6.	Activate your conda environment. In the command window, type:
    ```
    conda activate me564
    ```
7. Install the EESLib package from PyPi
    ```
    pip install eeslib
    ```
8. Automatic PDF reports are created from EESLib using LaTeX. This requires two tools to be installed on your computer that generate the reports. 
    *	Download and install the miktex compiler from https://miktex.org/download 
    *	Miktex uses Perl to run. Download and install Perl from https://www.perl.org/get.html
    The ‘Strawberry Perl’ version is recommended for Windows. 


### Install from source
Use this option if you are going to make local changes to the EESLib package source code.
```bash
git clone https://github.com/uw-esolab/eeslib.git
cd eeslib
pip install -e .
```

## Usage

Import the library modules as needed:

```python
from eeslib import fluid_properties as fp
from eeslib import internal_flow as iflow
from eeslib import functions as fn

# Get water properties at 100°C and 1 atm
rho = fp.density('Water', T=373.15, P=101325)
print(f"Density: {rho} kg/m³")

# Calculate Nusselt number for pipe flow
Nu, f = iflow.pipeflow_nd(Re=10000, Pr=7, LoverD=50, relRough=0.001)
print(f"Nusselt number: {Nu}, Friction factor: {f}")

# Convert units
temp_c = fn.converttemp('F', 'C', 212)
print(f"212°F = {temp_c}°C")
```

## Modules
| Module                 | Description                               |
| ---------------------- | ----------------------------------------- |
| `boiling.py`           | Boiling and condensing correlations       |
| `fluid_properties.py`  | Thermodynamic property calculations       |
| `internal_flow.py`     | Heat transfer in pipes and ducts          |
| `external_flow.py`     | External convection heat transfer         |
| `heat_exchangers.py`   | Heat exchanger analysis                   |
| `fin_efficiency.py`    | Extended surface heat transfer            |
| `radiation.py`         | Radiative heat transfer and view factors  |
| `functions.py`         | Utility functions, unit conversions       |
| `lookup_data.py`       | Interpolation and lookup tables           |
| `talbot_inversion.py`  | Numerical Laplace transform inversion     |

## License

Portions of this code are derived from Engineering Equation Solver (EES) under license restrictions and is intended for educational use at the University of Wisconsin-Madison.

## Contributing

This library is maintained for educational purposes. Please contact [the instructor](mailto:mjwagner2@wisc.edu) for contributions or modifications.

## Testing

EESLib includes a comprehensive test suite to ensure functionality and catch regressions.

### Running Tests

#### Install test dependencies:
```bash
pip install -e ".[dev]"
```

#### Run all tests:
```bash
python run_tests.py
```

#### Run specific test file:
```bash
python run_tests.py tests/test_fluid_properties.py
```

#### Run with coverage:
```bash
pip install pytest-cov
python -m pytest --cov=eeslib --cov-report=html
```

## Uploading a new version to Pypi

To upload a new version of EESLib to Pypi, follow the steps outlined in the [Python packaging tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/). 

The preferred packaging tool is `setuptools`. 

The most relevant steps are as follows:
1. Don't forget to update the code version number in `pyproject.toml` and in the `src/__init__.py` file.
1. Open a command window and navigate to the `eesdir` directory, such as
    ```bash
    cd C:\repositories\eeslib
    ```
2. Ensure the build and packaging tools are installed in the Conda environment that you're using. 
    The preferred method will install a developer tools, including build, pytest, and twine, specified in the pyproject.toml file in the eeslib directory:
    ```bash
    pip install .[dev]
    ```
    Alternatively, you can manually install packages:
    ```bash
    python -m pip install --upgrade build 
    python -m pip install --upgrade twine
    ```
3. Build the Python distributable
    ```bash
    python -m build
    ```
    This should create a folder `dist/` that contains a wheel (.whl) and tar.gz file. 
4. Upload the file to Pypi. You will need to have first created a username and API token, following the packing tutorial instructions. If uploading to the production server, use the command:
    ```bash
    twine upload dist/*
    ```

    If using the test server, use the command:
    ```bash
    python -m twine upload --repository testpypi dist/*
    ```

5. To install the package, activate the Conda environment (e.g., `conda activate me564`), and install. 
    If running from the production environment use:
    ```bash
    pip install eeslib
    ```

    If you have previous versions of `eeslib` already installed, force use of the most recent version using: 
    ```bash
    pip install --force-reinstall --upgrade eeslib
    ```


### Generate Sphinx documentation
After installing the dev prerequisites using `pip`, you can generate the documentation using the following steps:

1. Navigate to the `docs/` directory in bash. 

2. Generate the documentation stubs for the modules:
    ```bash
    sphinx-apidoc -o source ../src/eeslib/
    ```

3. Build the HTML
    ```bash
    make html
    ```

4. Open the documentation in a browser. The main index file is: `docs/build/html/index.html`


## References

- Engineering Equation Solver (EES)
- CoolProp library for fluid properties
- _Heat Transfer_ by Nellis & Klein, 2007