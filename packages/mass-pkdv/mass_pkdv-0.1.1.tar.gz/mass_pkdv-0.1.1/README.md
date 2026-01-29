# MASS: Product Kernel Density Visualization (KDV) Package

This package provides a C++ implementation of a **Product Kernel Density Visualization (KDV)** algorithm.

---

## Input Data Format

The input data file should be plain text:

```
n
x1 y1
x2 y2
...
xn yn
```

- `n` = number of data points  
- `x` and `y` in meters (or consistent units)

---

## Input Parameters (for Python wrapper or command line)

- `dim` : data dimensionality (default: 2)  
- `method` : algorithm method (0:SCAN, 1:SLAM, 2:MASS_CR, 3:MASS_OPT, 4:RQS_kd, 5:RQS_range)  
- `n_x`, `n_y` : number of discrete regions along x/y-axis  
- `k_type_x`, `k_type_y` : kernel type for x/y-axis (1:Epanechnikov, 2:Triangular, 3:Uniform)  
- `b_x_ratio`, `b_y_ratio` : bandwidth ratio for x/y-axis kernel

---

## Usage

### Python Wrapper

```python
from mass_pkdv import run_mass

run_mass(input_file, output_file)
```

Optionally, pass custom parameters:

```python
run_mass(input_file, output_file, dim=2, method=2, n_x=800, k_type_x=3, b_x_ratio=0.8, n_y=600, k_type_y=3, b_y_ratio=0.8)
```

### Command Line

```bash
bin\mass_pkdv.exe data\data.dat data\result.txt

