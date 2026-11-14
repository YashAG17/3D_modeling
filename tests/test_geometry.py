"""Sanity test on synthetic data (no images needed): python -m tests.test_geometry"""
import numpy as np
from src import geometry as G
from src.bundle_adjustment import bundle_adjust

rng = np.random.default_rng(1)
K = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1.0]])
X = rng.uniform(-1, 1, (300, 3)) + np.array([0, 0, 5])
R2 = G.rodrigues(np.array([0.02, 0.15, -0.03]))
t2 = np.array([-1.0, 0.05, 0.1])
x1 = G.project(K, np.eye(3), np.zeros(3), X) + rng.normal(0, 0.3, (300, 2))
x2 = G.project(K, R2, t2, X) + rng.normal(0, 0.3, (300, 2))
bad = rng.choice(300, 60, replace=False)           # 20% outliers
x2[bad] += rng.uniform(-80, 80, (60, 2))

F, inl = G.ransac_fundamental(x1, x2, thresh=1.5)
print("RANSAC inliers:", inl.sum(), "(true inliers 240); outliers wrongly kept:", inl[bad].sum())
assert inl.sum() > 200 and inl[bad].sum() < 10

E = G.essential_from_F(F, K, K)
xn1, xn2 = (x1 - K[:2, 2]) / 800, (x2 - K[:2, 2]) / 800
R, t, _ = G.recover_pose(E, xn1[inl], xn2[inl])
ang = np.degrees(np.arccos(np.clip((np.trace(R.T @ R2) - 1) / 2, -1, 1)))
dirc = abs(t @ (t2 / np.linalg.norm(t2)))
print(f"rotation error {ang:.3f} deg, translation direction cos {dirc:.4f}")
assert ang < 1.0 and dirc > 0.99

good = ~np.isin(np.arange(300), bad)
Xe = G.triangulate_dlt(K @ np.hstack([np.eye(3), np.zeros((3, 1))]),
                       K @ np.hstack([R2, t2.reshape(3, 1)]), x1[good], x2[good])
print("triangulation mean 3D error:", np.linalg.norm(Xe - X[good], axis=1).mean())
assert np.linalg.norm(Xe - X[good], axis=1).mean() < 0.05

# bundle adjustment: perturb cam 2 + points, expect error to drop
cams = np.array([[0, 0, 0, 0, 0, 0], np.r_[np.array([0.02, 0.15, -0.03]) + 0.02, t2 + 0.05]])
pts = X[good] + rng.normal(0, 0.05, (good.sum(), 3))
n = good.sum()
oc = np.r_[np.zeros(n, int), np.ones(n, int)]
op = np.r_[np.arange(n), np.arange(n)]
oxy = np.vstack([x1[good], x2[good]])
r0 = np.abs(__import__("src.bundle_adjustment", fromlist=["x"]).residuals(K, cams, pts, oc, op, oxy)).mean()
c2, p2 = bundle_adjust(K, cams, pts, oc, op, oxy)
r1 = np.abs(__import__("src.bundle_adjustment", fromlist=["x"]).residuals(K, c2, p2, oc, op, oxy)).mean()
print(f"BA mean |residual|: {r0:.2f} -> {r1:.2f} px")
assert r1 < r0 and r1 < 1.0
print("ALL TESTS PASSED")
