"""
Exponential Map Example
=======================

Compute the exponential map on the unit sphere.
"""

import numpy as np
from spheresmooth import exp_map   

# Example inputs
x = np.array([0.0, 0.0, 1.0])
v = np.array([1.0, 1.0, 0.0])

print("Input vectors:")
print("x =", x)
print("v =", v)

# Compute exponential map: exp_map(x, v)
result = exp_map(x, v)

print("\nExponential map exp_map(x, v):")
print(result)
