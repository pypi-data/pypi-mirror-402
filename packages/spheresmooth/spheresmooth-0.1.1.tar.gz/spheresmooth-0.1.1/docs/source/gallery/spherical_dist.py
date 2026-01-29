"""
Spherical Distance Example
==========================

Compute the spherical distance between two vectors on the unit sphere.
"""

import numpy as np
from spheresmooth import spherical_dist

# Example vectors
x = np.array([1.0, 0.0, 0.0])
y = np.array([0.0, 1.0, 0.0])

print("Input vectors:")
print("x =", x)
print("y =", y)

# Compute spherical distance
dist = spherical_dist(x, y)

print("\nSpherical distance spherical_dist(x, y):")
print(dist)
