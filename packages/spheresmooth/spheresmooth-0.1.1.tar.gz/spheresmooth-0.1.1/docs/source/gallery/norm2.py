"""
L2 Norm Example
===============

Compute the L2 (Euclidean) norm of a vector.
"""

import numpy as np
from spheresmooth import norm2

# Example vector
u = np.array([1.0, 2.0, 3.0])

print("Input vector:")
print("u =", u)

# Compute L2 norm
value = norm2(u)

print("\nL2 norm norm2(u):")
print(value)
