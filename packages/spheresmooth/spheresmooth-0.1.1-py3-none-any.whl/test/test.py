import numpy as np
from spheresmooth import (
    spherical_to_cartesian,
    cartesian_to_spherical,
    spherical_dist,
    piecewise_geodesic,
    penalized_linear_spherical_spline,
)

theta_phi = np.array([[np.pi/4, np.pi/3],
                      [np.pi/6, np.pi/4]])
xyz = spherical_to_cartesian(theta_phi)

print("변환된 Cartesian 좌표:")
print(xyz)

