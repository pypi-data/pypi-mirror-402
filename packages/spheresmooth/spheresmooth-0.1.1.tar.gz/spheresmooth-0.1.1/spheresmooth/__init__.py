"""
spheresmooth: Piecewise geodesic smoothing for spherical data (Python version)

This package is a full Python port of the R package `spheresmooth`.
"""

from .coords import (
    cartesian_to_spherical,
    spherical_to_cartesian,
    edp,
)

from .geometry import (
    dot,
    cross,
    norm2,
    normalize,
    normalize_lower,     
    spherical_dist,
    exp_map,
    geodesic,
    geodesic_lower,      
    piecewise_geodesic,
)

from .smoothing import (
    calculate_loss,
    knots_quantile,
    penalized_linear_spherical_spline,
)

from .loads import (load_apw,
                   load_goni,
                   load_world_map,
)


__all__ = [
    # coords
    "cartesian_to_spherical",
    "spherical_to_cartesian",
    "edp",
    # geometry
    "dot",
    "cross",
    "norm2",
    "normalize",
    "normalize_lower",
    "spherical_dist",
    "exp_map",
    "geodesic",
    "geodesic_lower",
    "piecewise_geodesic",
    # smoothing
    "calculate_loss",
    "knots_quantile",
    "penalized_linear_spherical_spline",
    # datasets
    "load_apw",
    "load_goni",
    "load_world_map",
]
