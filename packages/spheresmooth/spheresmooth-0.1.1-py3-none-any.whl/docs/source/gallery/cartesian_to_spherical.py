"""
Cartesian to Spherical Conversion Example
===============================

Convert Cartesian coordinates to spherical coordinates (theta, phi).
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
