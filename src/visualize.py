"""Visual outputs for results/presentation: PLY export, 3D plot, epipolar lines, match drawing."""
import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def save_ply(path, pts, colors):
    with open(path, "w") as f:
        f.write(f"ply\nformat ascii 1.0\nelement vertex {len(pts)}\n"
                "property float x\nproperty float y\nproperty float z\n"
                "property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n")
        for p, c in zip(pts, colors):
            f.write(f"{p[0]:.5f} {p[1]:.5f} {p[2]:.5f} {c[0]} {c[1]} {c[2]}\n")


def plot_reconstruction(path, pts, colors, centers):
    """Top-level 3D scatter of points + camera centres (outliers clipped by percentile)."""
    lo, hi = np.percentile(pts, 2, axis=0), np.percentile(pts, 98, axis=0)
    keep = ((pts >= lo) & (pts <= hi)).all(axis=1)
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(*pts[keep].T, c=colors[keep] / 255.0, s=1)
    ax.scatter(*centers.T, c="red", marker="^", s=40, label="cameras")
    ax.set_box_aspect(np.ptp(pts[keep], axis=0))
    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z"); ax.legend()
    ax.view_init(elev=-70, azim=-90)  # camera looks down +Z, image y points down
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def draw_matches(img1, img2, x1, x2, max_n=100, seed=0):
    idx = np.random.default_rng(seed).permutation(len(x1))[:max_n]
    h = max(img1.shape[0], img2.shape[0])
    canvas = np.zeros((h, img1.shape[1] + img2.shape[1], 3), np.uint8)
    canvas[:img1.shape[0], :img1.shape[1]] = img1
    canvas[:img2.shape[0], img1.shape[1]:] = img2
    off = img1.shape[1]
    for a, b in zip(x1[idx], x2[idx]):
        col = tuple(int(c) for c in np.random.default_rng(int(a[0])).integers(0, 255, 3))
        cv2.line(canvas, (int(a[0]), int(a[1])), (int(b[0]) + off, int(b[1])), col, 1)
    return canvas


def draw_epipolar_lines(img1, img2, x1, x2, F, n=12, seed=0):
    """For points in img1 draw the epipolar line l' = F x in img2 (and vice versa)."""
    idx = np.random.default_rng(seed).permutation(len(x1))[:n]
    a, b = img1.copy(), img2.copy()
    for p, q in zip(x1[idx], x2[idx]):
        col = tuple(int(c) for c in np.random.default_rng(int(p[0])).integers(0, 255, 3))
        l2 = F @ np.array([p[0], p[1], 1.0])        # line in image 2
        l1 = F.T @ np.array([q[0], q[1], 1.0])      # line in image 1
        for img, l, pt in ((b, l2, q), (a, l1, p)):
            w = img.shape[1]
            if abs(l[1]) < 1e-9:
                continue
            y0, y1 = -l[2] / l[1], -(l[2] + l[0] * w) / l[1]
            cv2.line(img, (0, int(y0)), (w, int(y1)), col, 1)
            cv2.circle(img, (int(pt[0]), int(pt[1])), 5, col, -1)
    return np.hstack([a, b[:a.shape[0]] if b.shape[0] >= a.shape[0] else b])


def plot_error_hist(path, errs):
    plt.figure(figsize=(5, 3.5))
    plt.hist(errs, bins=40, color="steelblue")
    plt.xlabel("reprojection error (px)"); plt.ylabel("# observations")
    plt.title(f"mean = {np.mean(errs):.2f} px")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
