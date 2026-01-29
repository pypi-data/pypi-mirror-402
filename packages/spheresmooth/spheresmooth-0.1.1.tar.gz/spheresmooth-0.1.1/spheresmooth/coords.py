"""
coords.py — Public coordinate transformation utilities for spheresmooth

This module provides the same functionality as the exported coordinate
transformation functions in the R package spheresmooth. The functions
here define the public-facing API for converting between Cartesian and
spherical coordinates and performing equal-distance projection (EDP). 
All lower-level geometric or optimization-related computations are
encapsulated inside internal modules such as _internal.py and geometry.py.

Features provided:

- Conversion between Cartesian and spherical coordinates (cartesian_to_spherical, spherical_to_cartesian)
- Equal-distance projection onto the plane (edp), matching the R implementation
- Input handling supporting both row-wise and column-wise formats
- Numerically stable trigonometric computations and normalization

This module works closely with geometry.py and smoothing.py and follows 
the coordinate-handling conventions of the original R implementation 
in spheresmooth.
"""

import numpy as np


def cartesian_to_spherical(x: np.ndarray, byrow: bool = True) -> np.ndarray:
    """
    Convert Cartesian coordinates to spherical coordinates (theta, phi).

    Parameters
    ----------
    x : array-like, shape (n, 3) or (3, n)
        Points in Cartesian coordinates (x, y, z).
    byrow : bool, default=True
        If True, rows are points. If False, columns are points.

    Returns
    -------
    theta_phi : ndarray, shape (n, 2)
        Spherical coordinates (theta, phi) with:
        - theta in [0, pi]   (inclination from +z)
        - phi   in [0, 2*pi) (azimuth)
    """
    arr = np.asarray(x, dtype=float)
    if not byrow:
        arr = arr.T

    if arr.ndim == 1:
        arr = arr[None, :]

    if arr.shape[1] != 3:
        raise ValueError("Input must have shape (n, 3) in Cartesian coordinates.")

    xs, ys, zs = arr[:, 0], arr[:, 1], arr[:, 2]
    r = np.linalg.norm(arr, axis=1)
    r = np.where(r == 0, 1.0, r)  # avoid division by zero

    # theta: inclination
    theta = np.arccos(np.clip(zs / r, -1.0, 1.0))
    # phi: azimuth
    phi = np.arctan2(ys, xs)
    phi = np.mod(phi, 2 * np.pi)

    return np.column_stack((theta, phi))


def spherical_to_cartesian(theta_phi: np.ndarray, byrow: bool = True) -> np.ndarray:
    """
    Convert spherical coordinates (theta, phi) to Cartesian coordinates (x, y, z).

    Parameters
    ----------
    theta_phi : array-like, shape (n, 2) or (2, n)
        Each row: (theta, phi), with theta in [0, pi], phi in [0, 2*pi).
    byrow : bool, default=True
        If True, rows are points. If False, columns are points.

    Returns
    -------
    xyz : ndarray, shape (n, 3)
        Cartesian coordinates on the unit sphere.
    """
    arr = np.asarray(theta_phi, dtype=float)
    if not byrow:
        arr = arr.T

    if arr.ndim == 1:
        arr = arr[None, :]

    if arr.shape[1] != 2:
        raise ValueError("Input must have shape (n, 2) in spherical coordinates.")

    theta, phi = arr[:, 0], arr[:, 1]
    sin_theta = np.sin(theta)

    x = sin_theta * np.cos(phi)
    y = sin_theta * np.sin(phi)
    z = np.cos(theta)

    return np.column_stack((x, y, z))


import numpy as np
from .coords import cartesian_to_spherical

def edp(p: np.ndarray) -> np.ndarray:
    """
    Equal-distance projection (EDP) of a point onto the xy-plane.
    
    This is a direct translation of the R function:

        edp = function(p) {
            theta_phi = cartesian_to_spherical(p)
            theta = theta_phi[1]
            phi = theta_phi[2]
            x = theta * cos(phi)
            y = theta * sin(phi)
            projection_p = c(x, y)
            return(projection_p)
        }

    Parameters
    ----------
    p : ndarray, shape (3,)
        Point in Cartesian coordinates.

    Returns
    -------
    ndarray, shape (2,)
        (x, y) coordinates after equal-distance projection.
    """

    p = np.asarray(p, float)
    if p.shape != (3,):
        raise ValueError("p must be a 3-dimensional vector.")

    theta, phi = cartesian_to_spherical(p)

    x = theta * np.cos(phi)
    y = theta * np.sin(phi)

    return np.array([x, y], float)
