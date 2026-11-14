"""Render a textured 'room corner' (back wall, floor, side wall) from N viewpoints by ray casting.
Gives ground-truth-known test images so the whole pipeline can be debugged without a dataset.
python -m tests.make_synthetic_scene --out images_synth"""
import argparse, os
import cv2
import numpy as np
from src import geometry as G


def make_texture(size=1024, seed=0):
    rng = np.random.default_rng(seed)
    tex = np.zeros((size, size, 3), np.float32)
    for sigma, amp in ((2, 1.0), (6, 1.0), (16, 0.8), (40, 0.6)):
        n = rng.normal(0, 1, (size, size, 3)).astype(np.float32)
        n = cv2.GaussianBlur(n, (0, 0), sigma)
        tex += amp * n / (n.std() + 1e-6)
    tex = (tex - tex.min()) / (tex.max() - tex.min())
    return (tex * 255).astype(np.uint8)


def render(R, C, K, tex, w, h):
    u, v = np.meshgrid(np.arange(w), np.arange(h))
    rays = np.stack([u, v, np.ones_like(u)], -1).reshape(-1, 3) @ np.linalg.inv(K).T
    d = rays @ R                      # world-space ray directions (R is world->cam, so d_w = R^T d_c)
    best = np.full(len(d), np.inf); uv = np.zeros((len(d), 2), np.float32)
    # planes: (normal, offset, uv-axes, extent)
    planes = [(np.array([0, 0, 1.0]), 6.0, (0, 1), 4.0),    # back wall z=6
              (np.array([0, 1.0, 0]), 1.5, (0, 2), 4.0),    # floor y=1.5 (y points down)
              (np.array([1.0, 0, 0]), -2.5, (2, 1), 4.0)]   # left wall x=-2.5
    for pi, (n, off, (a, b), ext) in enumerate(planes):
        denom = d @ n
        with np.errstate(divide="ignore", invalid="ignore"):
            lam = (off - C @ n) / denom
        P = C + lam[:, None] * d
        ok = (lam > 0) & (lam < best) & (np.abs(P[:, a]) < ext) & (np.abs(P[:, b]) < ext)
        best[ok] = lam[ok]
        uv[ok, 0] = (P[ok, a] + ext) / (2 * ext) * (tex.shape[1] - 1)
        uv[ok, 1] = (P[ok, b] + ext) / (2 * ext) * (tex.shape[0] - 1) if pi != 1 else \
                    (P[ok, b] / (2 * ext) + 0.5) * (tex.shape[0] - 1)
        uv[ok] += pi * 137  # different texture offset per plane
    uv = np.mod(uv, tex.shape[0] - 1)
    img = cv2.remap(tex, uv[:, 0].reshape(h, w), uv[:, 1].reshape(h, w), cv2.INTER_LINEAR)
    img[~np.isfinite(best).reshape(h, w)] = 0
    return img


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="images_synth"); ap.add_argument("--n", type=int, default=7)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    w, h, f = 640, 480, 600.0
    K = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1.0]])
    tex = make_texture()
    gt = []
    for i in range(a.n):
        x = -1.2 + 2.4 * i / (a.n - 1)
        C = np.array([x, -0.2 + 0.1 * np.sin(i), 0.0])
        yaw = -0.12 * x + 0.03 * np.cos(i)
        R = G.rodrigues(np.array([0.0, yaw, 0.0]))     # world->camera rotation
        cv2.imwrite(os.path.join(a.out, f"img_{i:02d}.png"), render(R, C, K, tex, w, h))
        gt.append(C)
    np.save(os.path.join(a.out, "gt_centers.npy"), np.array(gt))
    print("wrote", a.n, "images; focal =", f)
