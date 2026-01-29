"""
Dot Example
===================

Compute the dot product of two vectors.
"""

import numpy as np
from spheresmooth import dot  

# Example vectors
u = np.array([1.0, 2.0, 3.0])
v = np.array([4.0, 5.0, 6.0])

print("Input vectors:")
print("u =", u)
print("v =", v)

# Compute dot product: dot(u, v)
uv_dot = dot(u, v)

print("\nDot product dot(u, v):")
print(uv_dot)
