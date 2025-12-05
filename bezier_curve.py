import numpy as np

def alg_new_bezier(N, t, omega, W):
    h = 1.0
    Q = W[0]  # Początkowy punkt kontrolny

    for k in range(1, N + 1):
        b_k_minus_1 = 1 - t
        b_k = t

        if b_k == 0 or omega[k] == 0:
            continue

        h_k = (1 + omega[k - 1] * b_k_minus_1) / (h * omega[k] * b_k)
        if h_k == 0:
            continue

        h = 1 / h_k
        Q = ((1 - h) * Q[0] + h * W[k][0],
             (1 - h) * Q[1] + h * W[k][1])

    return Q

def bezier_curve(points, t_steps=1000, omega=None):
    if omega is None:
        omega = [1.0] * len(points)

    curve_points = []
    for t in np.linspace(0, 1, t_steps):
        curve_points.append(alg_new_bezier(len(points) - 1, t, omega, points))

    return np.array(curve_points)