"""
Geodesic Curve Example
======================

Compute a point on the geodesic curve connecting two points on the unit sphere.
"""

import numpy as np
from spheresmooth import geodesic_lower   

# Example inputs
t = 0.5
p = np.array([1.0, 0.0, 0.0])
q = np.array([0.0, 1.0, 0.0])
a = 0.0
b = 1.0

print("Inputs:")
print("t =", t)
print("p =", p)
print("q =", q)
print("a =", a, ", b =", b)

# Compute geodesic point
result = geodesic_lower(t, p, q, a, b)

print("\nGeodesic point at t = 0.5:")
print(result)
