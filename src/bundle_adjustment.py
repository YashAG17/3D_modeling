"""Unit 5 (5.4 Structure from Motion) - refinement step.
Bundle adjustment: jointly minimise reprojection error over camera poses and 3D points.
Non-linear least squares (Huber loss) with a sparse Jacobian pattern (scipy)."""
import numpy as np
from scipy.optimize import least_squares
from scipy.sparse import coo_matrix


def rotate(points, rvecs):
    """Vectorised Rodrigues: rotate points[i] by axis-angle rvecs[i]."""
    theta = np.linalg.norm(rvecs, axis=1)[:, None]
    with np.errstate(invalid="ignore", divide="ignore"):
        v = np.nan_to_num(rvecs / theta)
    dot = np.sum(points * v, axis=1)[:, None]
    c, s = np.cos(theta), np.sin(theta)
    return c * points + s * np.cross(v, points) + dot * (1 - c) * v


def residuals(K, cams, pts, obs_cam, obs_pt, obs_xy):
    Xc = rotate(pts[obs_pt], cams[obs_cam, :3]) + cams[obs_cam, 3:6]
    z = Xc[:, 2:3]
    z = np.where(np.abs(z) < 1e-8, 1e-8, z)
    u = K[0, 0] * Xc[:, 0:1] / z + K[0, 2]
    v = K[1, 1] * Xc[:, 1:2] / z + K[1, 2]
    return (np.hstack([u, v]) - obs_xy).ravel()


def bundle_adjust(K, cams, pts, obs_cam, obs_pt, obs_xy, max_nfev=30, huber_px=2.0, ftol=1e-6):
    """cams: (C,6) [rvec|t] world->camera, pts: (P,3). Camera 0 is held fixed (gauge).
    Returns refined (cams, pts)."""
    C, P, M = len(cams), len(pts), len(obs_cam)
    nc = 6 * (C - 1)

    def fun(params):
        cp = np.vstack([cams[:1], params[:nc].reshape(-1, 6)])
        pp = params[nc:].reshape(-1, 3)
        return residuals(K, cp, pp, obs_cam, obs_pt, obs_xy)

    # Sparsity: each residual depends on one camera (6 params) and one point (3 params)
    o = np.arange(M)
    rows, cols = [], []
    for r in range(2):
        for s in range(6):
            m = obs_cam > 0
            rows.append(2 * o[m] + r)
            cols.append(6 * (obs_cam[m] - 1) + s)
        for s in range(3):
            rows.append(2 * o + r)
            cols.append(nc + 3 * obs_pt + s)
    rows, cols = np.concatenate(rows), np.concatenate(cols)
    A = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(2 * M, nc + 3 * P)).tocsr()

    x0 = np.hstack([cams[1:].ravel(), pts.ravel()])
    # Stage 1: plain least squares to get close. Stage 2: Huber loss to down-weight bad tracks.
    # (Starting directly with a robust loss from a rough initialisation converges very slowly
    #  with the sparse LSMR solver - found while testing on synthetic data.)
    kw = dict(jac_sparsity=A, method="trf", x_scale="jac", ftol=ftol)
    res = least_squares(fun, x0, max_nfev=max_nfev, **kw)
    res = least_squares(fun, res.x, loss="huber", f_scale=huber_px, max_nfev=max_nfev, **kw)
    new_cams = np.vstack([cams[:1], res.x[:nc].reshape(-1, 6)])
    return new_cams, res.x[nc:].reshape(-1, 3)
