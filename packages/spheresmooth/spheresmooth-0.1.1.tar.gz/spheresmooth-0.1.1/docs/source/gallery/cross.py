"""
Cross Product Example
======================================

Compute the cross product of two vectors.
"""

import numpy as np
from spheresmooth import cross

# Example vectors
u = np.array([1.0, 0.0, 0.0])   # (1, 0, 0)
v = np.array([0.0, 1.0, 0.0])   # (0, 1, 0)

print("Input vectors:")
print("u =", u)
print("v =", v)

# Compute cross product (u × v)
uv_cross = cross(u, v)

print("\nCross product u × v:")
print(uv_cross)
