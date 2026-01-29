# robustbase-py

A Python port of the R `robustbase` package.

## Description

This package implements robust statistical methods, primarily focusing on robust regression (LMROB) as implemented in the R `robustbase` package. It provides MM-estimators initialized by S-estimators for high breakdown point and efficiency.

## Installation

```bash
pip install robustbase-py-optimized
```

## Usage

```python
import numpy as np
from robustbase import LMROB

# Generate synthetic data with outliers
n = 100
p = 3
rng = np.random.default_rng(42)
X = rng.standard_normal((n, p))
beta_true = np.array([1.0, 2.0, 0.5])
y = X @ beta_true + rng.standard_normal(n)

# Contaminate data (outliers)
y[:10] = 100.0

# Fit Robust Linear Regression
model = LMROB(method='MM', psi='bisquare')
model.fit(X, y)

print("Estimated Coefficients:", model.coef_)
print("True Coefficients:", beta_true)
print("Robust Scale:", model.scale_)
```

## Features

- **LMROB**: MM-estimator regression (S-init).
- **Psi Functions**: Bisquare, Huber.
- **Fast-S Algorithm**: For robust scale estimation and initialization.

## License

GPL-3.0
