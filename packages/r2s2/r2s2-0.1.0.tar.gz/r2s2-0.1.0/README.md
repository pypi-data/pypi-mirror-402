# Relativistic Reference System Service (R2S2)

The R2S2 Python package provides a systematic solution for relativistic spacetime coordinate transformations in the cislunar space.

## Features

The core functions encapsulated in R2S2 package enable bidirectional and strictly IAU-resolution-compliant transformation calculations between any two of the six commonly used spacetime coordinates across three reference systems in the cislunar space:
- Barycentric Celestial Reference System (BCRS)
- Geocentric Celestial Reference System (GCRS)
- Lunar Celestial Reference System (LCRS)

## Documentation

For detailed information, please refer to the package documentation:
- Chinese version: [中文版PDF](docs/r2s2-manual-zh.pdf).

## Dependencies

R2S2 depends on the following Python library:
- [numpy](https://numpy.org/)
- [calcephpy](https://calceph.imcce.fr/)

Data files for the following ephemerides are required:
- Planetary and lunar ephemeris with a built-in earth time ephemeris.

  We recommend DE440 (`de440t.bsp` variant, note the `t` for built-in time ephemeris), which is available at JPL website with [this link](https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de440t.bsp).
- Lunar time ephemeris.

  The lunar time ephemeris, [LTE440](https://github.com/xlucn/LTE440), is developed by our team and included in R2S2 package. No manually downloads are required.

## Installation

The detailed installation steps are as follows:

1. Install calcephpy

   For 64-bit windows systems with Python 3.10 to 3.14, we provide [the wheel packages](https://github.com/r2s2-astro/r2s2/releases/tag/python-calcephpy) of calcephpy v4.0.5 for easy installation
   ```sh
   pip install calcephpy-4.0.5-cp314-cp314-win_amd64.whl
   ```

   For other Python versions or OSes, the package can be installed from PyPi with `pip install calcephpy`. But it needs locally building as described in the [official install instructions](https://calceph.imcce.fr/docs/4.0.5/html/python/calceph.install.pythonusage.html#instructions). We also provide a step-by-step guide [here](docs/calceph.md).

2. Install R2S2

   The R2S2 package can be installed with pip
   ```sh
   pip install r2s2
   ```
   This will install its dependencies, and install the R2S2 package.

## Quick Start

Take transformation from lunar coordinates (TCL, Y) to barycentric (TCB, x) as an example

1. Import necessary Python packages
   ```py
   import numpy as np
   import R2S2
   ```
1. Import the local planetary ephemeris file containing the time ephemeris (note: modify the actual file path accordingly).
   ```py
   R2S2.init_E("/path/to/de440t.bsp")
   ```
1. Input the integer and fractional parts of the Julian Day in Lunar Coordinate Time (TCL), in days. The following corresponds to approximately 2026-01-04 11:23:39 TCL.
   ```py
   jd1 = 2460094
   jd2 = 0.9747569458346726
   ```
1. Input the spatial coordinates in the selenocentric system compatible with TCL, in kilometers.
   ```py
   Y = np.array([3000, 1813, 454])
   ```
1. Call the `TCL2TCB` function in R2S2 to compute the transformation from (TCL, Y) to (TCB, x), where `Delta_t` and `Delta_x` represent the iterative accuracy of time and space transformations, with units of seconds and kilometers respectively.
   ```py
   TCB1, TCB2, x = R2S2.TCL2TCB(jd1, jd2, Y, Delta_t = 10**(-9), Delta_x = 10**(-6))
   ```

Output should be
```py
TCB1 =  2460094
TCB2 =  0.9750082547331026
x =  [-5.72776989e+07 -1.29690213e+08 -5.61695394e+07]
```
