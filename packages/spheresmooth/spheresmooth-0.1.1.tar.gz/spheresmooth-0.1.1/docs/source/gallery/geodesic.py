"""
Geodesic Path Example
=====================

Compute multiple points along the geodesic curve between two points on the unit sphere.
"""

import numpy as np
from spheresmooth import geodesic   

# Example inputs
t = np.array([0.25, 0.5, 0.75])
p = np.array([1.0, 0.0, 0.0])
q = np.array([0.0, 1.0, 0.0])
a = 0.0
b = 1.0

print("Inputs:")
print("t =", t)
print("p =", p)
print("q =", q)
print("a =", a, ", b =", b)

# Compute the geodesic curve at multiple time points
gamma = geodesic(t, p, q, a, b)

print("\nGeodesic points at t = [0.25, 0.5, 0.75]:")
print(gamma)
