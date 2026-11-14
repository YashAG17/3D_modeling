"""Compare our camera centres with COLMAP's (validation + presentation 'Result' slide).
1) colmap automatic_reconstructor --workspace_path ws --image_path images
2) colmap model_converter --input_path ws/sparse/0 --output_path ws/txt --output_type TXT
3) python evaluate_vs_colmap.py --ours output/model.npz --colmap_txt ws/txt/images.txt
Compares camera centres after a similarity (Umeyama) alignment -> RMSE."""
import argparse
import numpy as np


def quat_to_R(q):
    w, x, y, z = q
    return np.array([[1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
                     [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
                     [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)]])


def read_colmap_centers(path):
    centers = {}
    lines = [l for l in open(path) if not l.startswith("#") and l.strip()]
    for l in lines[0::2]:  # every second line is the 2D point list
        p = l.split()
        q, t, name = np.array(p[1:5], float), np.array(p[5:8], float), " ".join(p[9:])
        centers[name] = -quat_to_R(q).T @ t
    return centers


def umeyama(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0)
    xs, xd = src - mu_s, dst - mu_d
    U, D, Vt = np.linalg.svd(xd.T @ xs / len(src))
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    s = np.trace(np.diag(D) @ S) / ((xs ** 2).sum() / len(src))
    return s, R, mu_d - s * R @ mu_s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", default="output/model.npz")
    ap.add_argument("--colmap_txt", required=True)
    a = ap.parse_args()
    d = np.load(a.ours)
    ours = {d["names"][i]: c for i, c in zip(d["reg_ids"], d["centers"])}
    ref = read_colmap_centers(a.colmap_txt)
    common = sorted(set(ours) & set(ref))
    print(f"{len(common)} common cameras")
    src, dst = np.array([ours[n] for n in common]), np.array([ref[n] for n in common])
    s, R, t = umeyama(src, dst)
    aligned = s * (R @ src.T).T + t
    rmse = np.sqrt(((aligned - dst) ** 2).sum(1).mean())
    diag = np.linalg.norm(dst.max(0) - dst.min(0))
    print(f"Camera-centre RMSE after alignment: {rmse:.4f}  ({100 * rmse / diag:.2f}% of COLMAP scene extent)")
