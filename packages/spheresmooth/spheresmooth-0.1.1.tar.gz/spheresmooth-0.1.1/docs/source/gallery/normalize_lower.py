"""
Normalize Vector Example
========================

Normalize a vector by dividing by its L2 norm.
"""

import numpy as np
from spheresmooth import normalize_lower

# Example vector
v = np.array([1, 2, 3, 4, 5, 6])

print("Input vector:")
print("v =", v)

# Normalize
v_norm = normalize_lower(v)

print("\nNormalized vector normalize_lower(v):")
print(v_norm)
