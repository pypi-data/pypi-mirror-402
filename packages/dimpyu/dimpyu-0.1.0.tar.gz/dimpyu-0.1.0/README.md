# DimPyU

A lightweight, flexible Python library for handling physical units, supporting arithmetic operations, dimensional analysis, and smart conversions.

## Features

-   **Intuitive Syntax**: `10 * reg.km` or `reg.parse("10 km")`
-   **Arithmetic**: Add, substract, multiply, and divide quantities (`m/s`, `kg * m/s^2`).
-   **Conversions**: Easily convert between compatible units (`val.to('km')`).
-   **SI Prefixes**: Automatically handles prefixes like `micro`, `giga`, `nano` (e.g. `micrometer`).
-   **Numpy Support**: Seamlessly works with Numpy arrays for high-performance calculations on vectors.
-   **Physical Constants**: Includes standard constants like Speed of Light ($c$), Gravity ($g_0$), etc.

## Installation

### From Source (Local)
```bash
pip install .
```

### From GitHub
You can install directly from your repository:
```bash
pip install git+https://github.com/YOUR_USERNAME/dimpyu.git
```

### From PyPI (Coming working)
```bash
pip install dimpyu
```

## Usage

```python
from dimpyu import UnitRegistry

# Initialize registry (loads default units)
reg = UnitRegistry()

# 1. Simple Quantity Creation
distance = 10 * reg.km
time = 0.5 * reg.hr
speed = distance / time
print(speed)                # 20.0 km / hr
print(speed.to('m/s'))      # 5.555... m / s

# 2. String Parsing
q = reg.parse("50 kg * m / s^2")
print(q)                    # 50.0 kg m/s^2
print(q.to('N'))            # 50.0 N

# 3. Array / Numpy Support
lengths = [1, 2, 3] * reg.meter
print(lengths.to('cm'))     # [100., 200., 300.] centimeter

# 4. Physical Constants
from dimpyu import constants
energy = constants.h * constants.c / (500 * reg.nm)
print(energy.to('J'))
```

## Project Structure

-   `dimpyu/`: Core package code.
-   `main.py`: Demo script.
-   `fluid_mechanics_example.py`: Example solution for a pump calculation.
-   `heat_transfer_example.py`: Example solution for a heat transfer problem.

## License

MIT
