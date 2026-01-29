import numpy as np
from spheresmooth import (
    spherical_to_cartesian,
    cartesian_to_spherical,
    spherical_dist,
    piecewise_geodesic,
)

# Spherical coordinates (theta, phi)
theta_phi = np.array([
    [np.pi / 4, np.pi / 3],
    [np.pi / 6, np.pi / 4]
])

# Convert to Cartesian coordinates on the unit sphere
xyz = spherical_to_cartesian(theta_phi)

# Compute geodesic distance between points
dist = spherical_dist(xyz[0], xyz[1])

# Fit a piecewise geodesic curve
curve = piecewise_geodesic(xyz)

print("Geodesic distance:", dist)
print("Smoothed curve:", curve)
