"""
Quantile-based Knot Generator Example
=====================================

Generate knot locations based on quantiles of time points.
"""

import numpy as np
from spheresmooth import knots_quantile   

# Example input
x = np.linspace(0.0, 1.0, 100)     # time points
dimension = 10                     # number of knots

print("Inputs:")
print("x: 0 to 1, length 100")
print("dimension =", dimension)

# Generate knots
knots = knots_quantile(x, dimension)

print("\nGenerated knots:")
print(knots)
