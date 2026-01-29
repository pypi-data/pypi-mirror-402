"""
Cartesian → Spherical Example 1
===============================

This example converts two 3D Cartesian points into spherical coordinates.
"""

import numpy as np
from spheresmooth import cartesian_to_spherical

# Example 1 data
cartesian_points1 = np.array([
    [1/np.sqrt(3),  1/np.sqrt(3),  1/np.sqrt(3)],
    [-1/np.sqrt(3), 1/np.sqrt(3), -1/np.sqrt(3)],
])

print("Input Cartesian points:")
print(cartesian_points1)

theta_phi = cartesian_to_spherical(cartesian_points1)
print("\nOutput spherical coordinates (theta, phi):")
print(theta_phi)
