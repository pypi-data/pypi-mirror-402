"""
Spherical to Cartesian Conversion Example
=========================================

Convert spherical coordinates (theta, phi) to Cartesian coordinates.
"""

import numpy as np
from spheresmooth import spherical_to_cartesian

# Example spherical coordinates
theta_phi = np.array([
    [np.pi / 4, np.pi / 3],
    [np.pi / 6, np.pi / 4]
])

print("Input spherical coordinates (theta, phi):")
print(theta_phi)

# Convert to Cartesian
cartesian = spherical_to_cartesian(theta_phi)

print("\nConverted Cartesian coordinates (x, y, z):")
print(cartesian)
