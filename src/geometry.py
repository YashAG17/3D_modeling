"""Unit 5 (5.1 Epipolar geometry, 5.3 Triangulation) + Unit 3 (3.5 RANSAC).
Everything here is implemented from scratch with NumPy."""
import numpy as np


# ---------- Rotation helpers (Unit 1.3: geometric transformations) ----------
def rodrigues(rvec):
    """Axis-angle (3,) -> rotation matrix (3,3)."""
    theta = np.linalg.norm(rvec)
    if theta < 1e-12:
        return np.eye(3)
    k = rvec / theta
    Kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(theta) * Kx + (1 - np.cos(theta)) * Kx @ Kx


def skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


# ---------- Fundamental matrix: normalised 8-point + RANSAC ----------
def normalize_points(pts):
    """Hartley normalisation: centroid -> origin, mean distance -> sqrt(2)."""
    c = pts.mean(axis=0)
    d = np.sqrt(((pts - c) ** 2).sum(axis=1)).mean()
    s = np.sqrt(2) / max(d, 1e-12)
    T = np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1.0]])
    ph = np.c_[pts, np.ones(len(pts))]
    return (T @ ph.T).T[:, :2], T


def eight_point(x1, x2):
    """Estimate F with x2^T F x1 = 0 from >=8 correspondences (pixel coords)."""
    n1, T1 = normalize_points(x1)
    n2, T2 = normalize_points(x2)
    A = np.stack([n2[:, 0] * n1[:, 0], n2[:, 0] * n1[:, 1], n2[:, 0],
                  n2[:, 1] * n1[:, 0], n2[:, 1] * n1[:, 1], n2[:, 1],
                  n1[:, 0], n1[:, 1], np.ones(len(n1))], axis=1)
    _, _, Vt = np.linalg.svd(A)
    F = Vt[-1].reshape(3, 3)
    U, S, Vt = np.linalg.svd(F)
    S[2] = 0  # enforce rank 2
    F = U @ np.diag(S) @ Vt
    F = T2.T @ F @ T1  # denormalise
    return F / np.linalg.norm(F)


def sampson_error(F, x1, x2):
    """First-order geometric error (squared pixels) of each correspondence."""
    h1 = np.c_[x1, np.ones(len(x1))]
    h2 = np.c_[x2, np.ones(len(x2))]
    Fx1 = h1 @ F.T
    Ftx2 = h2 @ F
    num = np.sum(h2 * Fx1, axis=1) ** 2
    den = Fx1[:, 0] ** 2 + Fx1[:, 1] ** 2 + Ftx2[:, 0] ** 2 + Ftx2[:, 1] ** 2
    return num / (den + 1e-12)


def ransac_fundamental(x1, x2, thresh=1.0, max_iters=2000, conf=0.999, seed=0):
    """RANSAC around the 8-point algorithm. Returns F, inlier boolean mask."""
    rng = np.random.default_rng(seed)
    N = len(x1)
    if N < 8:
        return None, np.zeros(N, bool)
    best_inl, best_n = np.zeros(N, bool), 0
    n_iter, i = max_iters, 0
    while i < n_iter:
        i += 1
        idx = rng.choice(N, 8, replace=False)
        F = eight_point(x1[idx], x2[idx])
        inl = sampson_error(F, x1, x2) < thresh ** 2
        if inl.sum() > best_n:
            best_n, best_inl = int(inl.sum()), inl
            w = best_n / N  # adaptive iteration count
            n_iter = min(max_iters, max(50, int(np.log(1 - conf) / np.log(1 - w ** 8 + 1e-12))))
    if best_n < 8:
        return None, best_inl
    F = eight_point(x1[best_inl], x2[best_inl])  # refit on all inliers
    return F, sampson_error(F, x1, x2) < thresh ** 2


# ---------- Essential matrix & pose ----------
def essential_from_F(F, K1, K2):
    return K2.T @ F @ K1


def decompose_essential(E):
    """4 candidate (R, t) from E = U diag(1,1,0) V^T."""
    U, _, Vt = np.linalg.svd(E)
    if np.linalg.det(U) < 0:
        U[:, -1] *= -1
    if np.linalg.det(Vt) < 0:
        Vt[-1] *= -1
    W = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1.0]])
    R1, R2 = U @ W @ Vt, U @ W.T @ Vt
    t = U[:, 2]
    return [(R1, t), (R1, -t), (R2, t), (R2, -t)]


def triangulate_dlt(P1, P2, x1, x2):
    """Linear (DLT) triangulation of N points. P: 3x4. x: (N,2). Returns (N,3)."""
    N = len(x1)
    A = np.empty((N, 4, 4))
    A[:, 0] = x1[:, 0:1] * P1[2] - P1[0]
    A[:, 1] = x1[:, 1:2] * P1[2] - P1[1]
    A[:, 2] = x2[:, 0:1] * P2[2] - P2[0]
    A[:, 3] = x2[:, 1:2] * P2[2] - P2[1]
    _, _, Vt = np.linalg.svd(A)
    X = Vt[:, -1, :]
    w = np.where(np.abs(X[:, 3:4]) < 1e-12, 1e-12, X[:, 3:4])
    return X[:, :3] / w


def recover_pose(E, xn1, xn2):
    """Cheirality check: keep the (R,t) that puts most points in front of both cameras.
    xn1, xn2 are NORMALISED coordinates. Returns R, t, mask of points in front."""
    P1 = np.hstack([np.eye(3), np.zeros((3, 1))])
    best, best_n = None, -1
    for R, t in decompose_essential(E):
        P2 = np.hstack([R, t.reshape(3, 1)])
        X = triangulate_dlt(P1, P2, xn1, xn2)
        z1 = X[:, 2]
        z2 = (R @ X.T).T[:, 2] + t[2]
        good = (z1 > 0) & (z2 > 0)
        if good.sum() > best_n:
            best_n, best = int(good.sum()), (R, t, good)
    return best


# ---------- Projection / error ----------
def project(K, R, t, X):
    Xc = (R @ X.T).T + t.reshape(1, 3)
    x = (K @ Xc.T).T
    with np.errstate(divide="ignore", invalid="ignore"):
        return x[:, :2] / x[:, 2:3]


def reproj_error(K, R, t, X, x):
    return np.linalg.norm(project(K, R, t, X) - x, axis=1)


def triangulation_angle(X, C1, C2):
    """Angle (deg) between the two viewing rays; small angle = unreliable depth."""
    a, b = X - C1, X - C2
    c = np.sum(a * b, axis=1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) + 1e-12)
    return np.degrees(np.arccos(np.clip(c, -1, 1)))
