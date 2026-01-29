"""
Cartesian → Spherical Example 2
===============================

Basic axes-aligned points example.
"""

import numpy as np
from spheresmooth import cartesian_to_spherical

# Example 2 data
cartesian_points2 = np.array([
    [1, 0, 0],  # +x axis
    [0, 1, 0],  # +y axis
    [0, 0, 1],  # +z axis
])

print("Input Cartesian points:")
print(cartesian_points2)

theta_phi = cartesian_to_spherical(cartesian_points2)
print("\nOutput spherical coordinates (theta, phi):")
print(theta_phi)
