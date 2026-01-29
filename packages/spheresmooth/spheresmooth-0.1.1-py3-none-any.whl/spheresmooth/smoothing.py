"""
This module provides the core functionality for penalized spherical smoothing,
equivalent to the exported functions in the R package `spheresmooth`.

The functions defined here implement the public-facing API of the Python
version, while internal mathematical components (loss gradients, penalty
gradients, jump operators, Acos utilities, etc.) are delegated to `_internal.py`.

Main features include:

- Construction of quantile-based knot locations (`knots_quantile`)
- Computation of geodesic loss on the sphere (`calculate_loss`)
- Full penalized spline fitting procedure
  (`penalized_linear_spherical_spline`)
- Integration with geometric utilities such as:
    * spherical distance (`spherical_dist`)
    * exponential map (`exp_map`)
    * geodesic interpolation (`geodesic`, `geodesic_lower`)
    * piecewise geodesic curve construction (`piecewise_geodesic`)
    * coordinate transformations (spherical/cartesian)

This module works closely with `geometry.py` and `_internal.py`, reproducing
the piecewise-geodesic smoothing structure of the original R implementation
from the `spheresmooth` package.
"""

import numpy as np

from ._internal import (
    _jump_linear,
    _Rgradient_loss_linear_spline,
    _R_gradient_penalty,
    _Acos,
)
from .geometry import spherical_dist, piecewise_geodesic, normalize, exp_map
from .coords import spherical_to_cartesian, cartesian_to_spherical


def calculate_loss(y: np.ndarray, gamma: np.ndarray) -> float:
    """
    Calculate loss based on squared spherical distances
    between observed values and predicted values on the curve.

    Parameters
    ----------
    y : ndarray, shape (n, 3)
        Observed points on the sphere (Cartesian).
    gamma : ndarray, shape (n, 3)
        Predicted points on the sphere (Cartesian).

    Returns
    -------
    float
        Loss value (sum of squared spherical distances).
    """
    y = np.asarray(y, float)
    gamma = np.asarray(gamma, float)
    
    dists = np.array([
        spherical_dist(y[i], gamma[i])**2
        for i in range(y.shape[0])
    ])

    return 0.5 * np.sum(dists)


def knots_quantile(x: np.ndarray, dimension: int, tiny: float = 1e-5) -> np.ndarray:
    """
    Exact Python replication of R's knots_quantile() with quantile(type = 3).

    Parameters
    ----------
    x : 1D array-like
        Time points.
    dimension : int
        Number of control points = number of knots.
    tiny : float
        Small offset for extending boundaries.

    Returns
    -------
    knots : ndarray, shape (dimension,)
    """

    x = np.asarray(np.unique(x), float)

    if dimension < 2:
        dimension = 2

    number_interior = dimension - 2

    # Case 1: No interior knots
    if number_interior <= 0:
        return np.array([x.min() - tiny, x.max() + tiny])

    # interior quantile positions: probs = 1/(m+1), 2/(m+1), ..., m/(m+1)
    probs = np.arange(1, number_interior + 1) / (number_interior + 1)

    # R quantile type = 3  (linear interpolation based on rounding)
    def quantile_type3(values, p):
        n = len(values)
        # position index in R type=3: floor(n*p + 0.5)
        h = np.floor(n * p + 0.5).astype(int)
        h = np.clip(h, 1, n)
        return values[h - 1]

    # exclude first and last x in interior knot computation (same as R)
    x_mid = x[1:-1]

    interior = np.array([quantile_type3(x_mid, p) for p in probs])

    # Construct full knot vector
    knots = np.concatenate([
        [x.min() - tiny],
        interior,
        [x.max() + tiny]
    ])

    return knots


def penalized_linear_spherical_spline(
    t,
    y,
    initial_control_points=None,
    dimension=None,
    initial_knots=None,
    lambdas=None,
    step_size=1.0,
    maxiter=1000,
    epsilon_iter=1e-3,
    jump_eps=1e-4,
    verbose=False
):
    """
    Fully implemented Python version of the R function
    penalized_linear_spherical_spline().
    """

    t = np.asarray(t, float)
    y = np.asarray(y, float)
    n = len(t)

    if lambdas is None:
        raise ValueError("lambdas must be provided.")

    lambdas = np.asarray(lambdas, float)
    number_lambdas = len(lambdas)

    # ----------------------------
    # Initialize control points 
    # ----------------------------
    if initial_control_points is None:
        if dimension is None:
            raise ValueError("dimension must be specified when initial_control_points is None.")

        # R: seq(1, n, length=dimension)
        # Python 동일: float → round → int index
        idx_float = np.linspace(1, n, num=dimension)
        idx = np.floor(idx_float - 1).astype(int)

        control_points = y[idx].copy()

    else:
        control_points = np.asarray(initial_control_points, float)
        if dimension is None:
            dimension = control_points.shape[0]

    # ----------------------------
    # Initialize knots
    # ----------------------------
    if initial_knots is None:
        raise ValueError("initial_knots must be provided.")
    knots = np.asarray(initial_knots, float)

    # ----------------------------
    # Prepare storage
    # ----------------------------
    temp_cp = control_points.copy()
    bic_list = np.zeros(number_lambdas)
    dimension_list = np.zeros(number_lambdas, dtype=int)

    # Initial gamma and loss
    gamma = piecewise_geodesic(t, temp_cp, knots)
    Rlambda = calculate_loss(y, gamma)

    if lambdas[0] > 0:
        Rlambda += lambdas[0] * np.sqrt(np.sum(np.sum(_jump_linear(control_points, knots)**2, axis=1)))

    Rlambda_stored = np.inf

    fit_list = []

    # ==================================================
    # Loop over lambda values
    # ==================================================
    for lam_idx in range(number_lambdas):
        lam = lambdas[lam_idx]
        if verbose:
            print(f"\n[Lambda {lam_idx+1}/{number_lambdas}] λ = {lam}")

        number_penalty = control_points.shape[0] - 2

        # ==================================================
        # Block Coordinate Descent outer loop
        # ==================================================
        for it in range(maxiter):

            if verbose:
                print(f" Iteration {it+1}")

            # ------------------------------------
            # Update control points
            # ------------------------------------
            for j in range(1, dimension+1):
                idx = j - 1

                Rgrad_loss = _Rgradient_loss_linear_spline(y, t, control_points, knots, idx+1)
                R_pen = _R_gradient_penalty(control_points, knots, idx+1)

                Rgrad_f = Rgrad_loss + lam * R_pen
                R_step = Rlambda
                step = step_size

                for _ in range(100):
                    cp_tmp = exp_map(control_points[idx], -Rgrad_f * step)
                    cp_tmp /= np.linalg.norm(cp_tmp)

                    temp_cp[idx] = cp_tmp
                    gamma = piecewise_geodesic(t, temp_cp, knots)
                    Rlambda_new = calculate_loss(y, gamma)

                    if number_penalty > 0 and lam > 0:
                        Rlambda_new += lam * np.sqrt(
                            np.sum(np.sum(_jump_linear(temp_cp, knots)**2, axis=1))
                        )

                    if Rlambda_new <= R_step:
                        break
                    step *= 0.5

                control_points[idx] = temp_cp[idx]
                Rlambda = Rlambda_new

            # ------------------------------------
            # Penalization pruning
            # ------------------------------------
            if number_penalty > 0 and lam > 0:
                jumps = _jump_linear(control_points, knots)
                jump_size = np.zeros(number_penalty)

                for k in range(number_penalty):
                    w = ((knots[k+2] - knots[k+1]) + (knots[k+1] - knots[k])) / 2
                    jump_size[k] = np.sum((w * jumps[k])**2)

                penalty_check = jump_size < jump_eps

                if verbose:
                    print(" jump_size =", jump_size)
                    print(" knots =", knots)

                if np.sum(penalty_check) > 0:
                    prune_idx = np.where(penalty_check)[0]

                    control_points = np.delete(control_points, prune_idx+1, axis=0)
                    knots = np.delete(knots, prune_idx+1)

                    dimension = control_points.shape[0]
                    number_penalty = dimension - 2
                    temp_cp = control_points.copy()

            # ------------------------------------
            # Convergence check
            # ------------------------------------
            gamma = piecewise_geodesic(t, temp_cp, knots)
            Rlambda_new = calculate_loss(y, gamma)

            if number_penalty > 0 and lam > 0:
                Rlambda_new += lam * np.sqrt(
                    np.sum(np.sum(_jump_linear(control_points, knots)**2, axis=1))
                )

            if verbose:
                print(" Rlambda =", Rlambda_new)

            if np.abs(Rlambda_new - Rlambda_stored) < epsilon_iter:
                break

            Rlambda_stored = Rlambda_new
            Rlambda = Rlambda_new

        # ----------------------------
        # Save results
        # ----------------------------
        gamma = piecewise_geodesic(t, temp_cp, knots)
        R = calculate_loss(y, gamma)

        dimension_list[lam_idx] = control_points.shape[0]
        bic_list[lam_idx] = n * np.log(R) + 3 * np.log(n) * control_points.shape[0]

        fit_list.append({
            "gamma": gamma,
            "control_points": control_points.copy(),
            "knots": knots.copy(),
            "dimension": control_points.shape[0],
            "lambda": lam,
        })

    return {
        "fits": fit_list,
        "bic_list": bic_list,
        "dimension_list": dimension_list
    }
