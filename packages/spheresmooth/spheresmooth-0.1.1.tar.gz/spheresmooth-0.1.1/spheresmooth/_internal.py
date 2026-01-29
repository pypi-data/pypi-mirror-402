import numpy as np

# ================================================================
# Safe numerical helpers
# ================================================================

def _restrict(x, lower, upper):
    x = np.asarray(x, float)
    x = np.where(x < lower, lower, x)
    x = np.where(x > upper, upper, x)
    return x


def _Acos(x):
    return np.arccos(_restrict(x, -1.0, 1.0))


def _Asin(x):
    return np.arcsin(_restrict(x, -1.0, 1.0))


def _Atan(y, x):
    y = np.asarray(y, float)
    x = np.asarray(x, float)
    out = np.zeros_like(y)

    mask0 = (x == 0)

    out[mask0 & (y > 0)] = np.pi / 2
    out[mask0 & (y < 0)] = 3 * np.pi / 2
    out[mask0 & (y == 0)] = 0

    mask1 = (y == 0) & (x != 0)
    out[mask1 & (x > 0)] = 0
    out[mask1 & (x < 0)] = np.pi

    mask2 = ~(mask0 | (y == 0))
    absx = np.abs(x[mask2])
    absy = np.abs(y[mask2])
    theta = np.arctan2(absy, absx)

    r = np.zeros_like(theta)

    idx = (x[mask2] > 0) & (y[mask2] > 0)
    r[idx] = theta[idx]

    idx = (x[mask2] < 0) & (y[mask2] > 0)
    r[idx] = np.pi - theta[idx]

    idx = (x[mask2] < 0) & (y[mask2] < 0)
    r[idx] = np.pi + theta[idx]

    idx = (x[mask2] > 0) & (y[mask2] < 0)
    r[idx] = 2 * np.pi - theta[idx]

    out[mask2] = r
    return out


# ================================================================
# Omega (spherical -> Cartesian)
# ================================================================

def _omega(theta, phi):
    theta = np.asarray(theta, float)
    phi = np.asarray(phi, float)
    return np.column_stack([
        np.sin(theta) * np.cos(phi),
        np.sin(theta) * np.sin(phi),
        np.cos(theta)
    ])


# ================================================================
# Spherical distance utilities
# ================================================================

def _calculate_c_t(p_t, q_t):
    return np.linalg.norm(p_t - q_t, axis=1)


def _calculate_R_s(theta, s):
    if theta == 0:
        return 0.0
    return np.sin(theta * s) / np.sin(theta)


def _calculate_R_s_c_t(c_t, s):
    return np.array([
        _calculate_R_s(c_t[i], s[i])
        for i in range(len(s))
    ])


def _calculate_Q_s(theta, s):
    t = float(theta)
    s = float(s)
    return (np.sin(s * t) * np.cos(t) - s * np.cos(s * t) * np.sin(t)) / (np.sin(t) ** 3)


def _calculate_Apsi(psi):
    if psi == 0:
        return 0.0
    return psi / np.sin(psi)


def _calculate_projection_p(p, y):
    return y - p * np.dot(p, y)


# ================================================================
# Jump penalty for linear spline
# ================================================================

def _jump_linear(control_points, knots):
    cp = np.asarray(control_points, float)
    knots = np.asarray(knots, float)
    m = cp.shape[0] - 2

    jumps = np.zeros((m, 3))
    for j in range(m):
        p1 = cp[j]
        p2 = cp[j+1]
        p3 = cp[j+2]

        theta1 = _Acos(np.dot(p1, p2))
        theta2 = _Acos(np.dot(p2, p3))

        d1 = knots[j+1] - knots[j]
        d2 = knots[j+2] - knots[j+1]

        a = theta2 / (np.sin(theta2) * d2)
        c = theta1 / (np.sin(theta1) * d1)
        b1 = np.cos(theta2) * a
        b2 = np.cos(theta1) * c

        jumps[j] = a * p3 - (b1 + b2) * p2 + c * p1

    return jumps


# ================================================================
# Gradient for linear segment
# ================================================================

def _gradient_linear_point(t, control_points, index):
    p1 = control_points[0]
    p2 = control_points[1]

    theta = _Acos(np.dot(p1, p2))

    Q_t = _calculate_Q_s(theta, t)
    Q_1_t = _calculate_Q_s(theta, 1 - t)

    if index == 1:
        R_1_t = _calculate_R_s(theta, 1 - t)
        return (R_1_t * np.eye(3) +
                Q_1_t * np.outer(p2, p1) +
                Q_t * np.outer(p2, p2))

    elif index == 2:
        R_t = _calculate_R_s(theta, t)
        return (R_t * np.eye(3) +
                Q_1_t * np.outer(p1, p1) +
                Q_t * np.outer(p1, p2))

    else:
        return np.zeros((3, 3))


# ================================================================
# Rgradient_loss_point_linear
# ================================================================

def _Rgradient_loss_point_linear(y, t, control_points, index):
    from .geometry import geodesic
    gamma_t = geodesic(t, control_points[0], control_points[1], 0, 1)

    phi = _Acos(np.dot(y, gamma_t))
    grad_linear = _gradient_linear_point(t, control_points, index)
    proj = _calculate_projection_p(control_points[index-1], grad_linear @ y)

    Aphi = _calculate_Apsi(phi)
    return -Aphi * proj


# ================================================================
# Rgradient_loss_linear (sum of point-wise)
# ================================================================

def _Rgradient_loss_linear(y, t, control_points, index):
    total = np.zeros(3)
    for i in range(len(t)):
        total += _Rgradient_loss_point_linear(y[i], t[i], control_points, index)
    return total


# ================================================================
# Rgradient_loss_linear_spline
# ================================================================

def _Rgradient_loss_linear_spline(y, t, control_points, knots, index):
    J = control_points.shape[0]
    grad = np.zeros(3)

    # left segment
    if index > 1:
        left_knots = knots[index-2:index]
        cp_left = control_points[index-2:index]
        mask = (t >= left_knots[0]) & (t < left_knots[1])

        if mask.any():
            m = (t[mask] - left_knots[0]) / (left_knots[1] - left_knots[0])
            grad += _Rgradient_loss_linear(y[mask], m, cp_left, 2)

    # right segment
    if index < J:
        right_knots = knots[index-1:index+1]
        cp_right = control_points[index-1:index+1]
        mask = (t >= right_knots[0]) & (t < right_knots[1])

        if mask.any():
            m = (t[mask] - right_knots[0]) / (right_knots[1] - right_knots[0])
            grad += _Rgradient_loss_linear(y[mask], m, cp_right, 1)

    return grad


# ================================================================
# R_gradient_penalty
# ================================================================

def _R_gradient_penalty(control_points, knots, index):
    """
    Exact Python translation of R's R_gradient_penalty(), including all 3 cases.
    """

    cp = np.asarray(control_points, float)
    k = np.asarray(knots, float)
    m = cp.shape[0]

    # index in Python is 0-based
    # index in R is 1-based
    # So R's index j corresponds to Python's idx = j-1
    idx = index - 1

    R_grad = np.zeros(3)

    # ----------------------------------------------------------
    # CASE 1:  (R: if (index < dimension - 1))
    # Python: idx < m - 2
    # ----------------------------------------------------------
    if idx < m - 2:
        delta1 = k[idx+1] - k[idx]
        delta2 = k[idx+2] - k[idx+1]

        theta1 = _Acos(np.dot(cp[idx+1], cp[idx]))
        theta2 = _Acos(np.dot(cp[idx+2], cp[idx+1]))

        a_j_minus = theta1 / (np.sin(theta1) * delta1)
        a_j = theta2 / (np.sin(theta2) * delta2)
        b_j = np.cos(theta1) * a_j
        b_j_minus = np.cos(theta2) * a_j_minus

        d = (a_j_minus * cp[idx]
             - (b_j + b_j_minus) * cp[idx+1]
             + a_j * cp[idx+2])

        # compute A and B exactly as in R
        A = ((np.cos(theta1) * theta1 - np.sin(theta1)) /
             (np.sin(theta1)**3)) * a_j * np.dot(cp[idx], cp[idx+2]) + \
            ((np.cos(theta2) * np.cos(theta1) * np.sin(theta1)
              - np.cos(theta2)*theta1) /
             (np.sin(theta1)**3)) * a_j_minus - a_j_minus

        B = theta1 / np.sin(theta1) * a_j

        grad = (-(A*np.cos(theta1) + B*np.dot(cp[idx], cp[idx+2])) * cp[idx]
                + A*cp[idx+1]
                + B*cp[idx+2])

        grad = grad / (np.linalg.norm(d) * delta1)
        R_grad += grad

    # ----------------------------------------------------------
    # CASE 2: (R: if (index > 1 & index < dimension))
    # Python: idx > 0 and idx < m-1
    # ----------------------------------------------------------
    if idx > 0 and idx < m - 1:

        delta1 = k[idx] - k[idx-1]
        delta2 = k[idx+1] - k[idx]

        theta1 = _Acos(np.dot(cp[idx], cp[idx-1]))
        theta2 = _Acos(np.dot(cp[idx+1], cp[idx]))

        a_j_minus = theta1/(np.sin(theta1)*delta1)
        a_j = theta2/(np.sin(theta2)*delta2)
        b_j = np.cos(theta1)*a_j
        b_j_minus = np.cos(theta2)*a_j_minus

        d = (a_j_minus*cp[idx-1] -
             (b_j + b_j_minus)*cp[idx] +
             a_j*cp[idx+1])

        w1 = (np.cos(theta2)*theta2 - np.sin(theta2))/np.sin(theta2)**3
        w2 = (np.cos(theta1)*theta1 - np.sin(theta1))/np.sin(theta1)**3

        A1 = w1*(-np.cos(theta1)*np.cos(theta2)*a_j_minus
                 + np.dot(cp[idx-1], cp[idx+1])*a_j_minus) - a_j

        B1 = theta2*np.cos(theta2) / np.sin(theta2)

        A2 = w2*(-np.cos(theta2)*np.cos(theta1)*a_j
                 + np.dot(cp[idx-1], cp[idx+1])*a_j) - a_j_minus

        B2 = theta1*np.cos(theta1) / np.sin(theta1)

        grad = (
            (-(A1*np.cos(theta2) + B1*np.cos(theta1))*cp[idx]
             + A1*cp[idx+1]
             + B1*cp[idx-1]) / delta2
            +
            (-(A2*np.cos(theta1) + B2*np.cos(theta2))*cp[idx]
             + A2*cp[idx-1]
             + B2*cp[idx+1]) / delta1
        )

        grad = grad / np.linalg.norm(d)
        R_grad += grad

    # ----------------------------------------------------------
    # CASE 3: (R: if (index > 2))
    # Python: idx > 1
    # ----------------------------------------------------------
    if idx > 1:
        delta1 = k[idx-1] - k[idx-2]
        delta2 = k[idx] - k[idx-1]

        theta1 = _Acos(np.dot(cp[idx-1], cp[idx-2]))
        theta2 = _Acos(np.dot(cp[idx], cp[idx-1]))

        a_j_minus = theta1/(np.sin(theta1)*delta1)
        a_j = theta2/(np.sin(theta2)*delta2)
        b_j = np.cos(theta1)*a_j
        b_j_minus = np.cos(theta2)*a_j_minus

        d = (a_j_minus*cp[idx-2]
             - (b_j + b_j_minus)*cp[idx-1]
             + a_j*cp[idx])

        A = ((np.cos(theta2)*theta2 - np.sin(theta2)) /
             (np.sin(theta2)**3)) * a_j_minus * np.dot(cp[idx-2], cp[idx]) + \
            ((np.cos(theta1)*np.cos(theta2)*np.sin(theta2)
              - np.cos(theta1)*theta2) /
             (np.sin(theta2)**3)) * a_j_minus - a_j

        B = theta2/np.sin(theta2) * a_j_minus

        grad = (-(A*np.cos(theta2) + B*np.dot(cp[idx-2], cp[idx])) * cp[idx]
                + A*cp[idx-1]
                + B*cp[idx-2])

        grad = grad / (np.linalg.norm(d) * delta2)
        R_grad += grad

    return R_grad
