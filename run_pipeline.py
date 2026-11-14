"""Run the full mini-SfM pipeline:  python run_pipeline.py --images images --out output"""
import argparse
import os
import time
import cv2
import numpy as np
from src.camera import load_images, default_intrinsics
from src.features import extract_sift, harris_corners, dog_pyramid, dog_keypoints
from src.matching import match_all_pairs
from src.sfm import SfM
from src import geometry as G
from src import visualize as V


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", default="images")
    ap.add_argument("--out", default="output")
    ap.add_argument("--max_size", type=int, default=1600)
    ap.add_argument("--focal", type=float, default=None, help="focal length in pixels (after resize)")
    ap.add_argument("--window", type=int, default=None, help="only match images within +-window index")
    ap.add_argument("--fast", action="store_true", help="use OpenCV RANSAC instead of our own (faster)")
    ap.add_argument("--demos", action="store_true", help="save Harris / DoG demo images (Unit 3)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()

    print("[1/5] Loading images + camera model")
    names, imgs = load_images(a.images, a.max_size)
    h, w = imgs[0].shape[:2]
    K = default_intrinsics(w, h, a.focal)
    print(f"  {len(imgs)} images, {w}x{h}, K =\n{K}")

    print("[2/5] SIFT features")
    grays = [cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) for im in imgs]
    kps, descs = zip(*[extract_sift(g) for g in grays])
    print("  keypoints per image:", [len(k) for k in kps])
    if a.demos:
        vis = imgs[0].copy()
        for x, y in harris_corners(grays[0]):
            cv2.circle(vis, (int(x), int(y)), 2, (0, 0, 255), -1)
        cv2.imwrite(os.path.join(a.out, "demo_harris.jpg"), vis)
        vis = imgs[0].copy()
        for x, y, s in dog_keypoints(dog_pyramid(grays[0])):
            cv2.circle(vis, (int(x), int(y)), max(2, int(s * 1.5)), (0, 255, 0), 1)
        cv2.imwrite(os.path.join(a.out, "demo_dog.jpg"), vis)

    print("[3/5] Matching + RANSAC geometric verification")
    matches = match_all_pairs(list(kps), list(descs), use_opencv=a.fast, window=a.window)
    if not matches:
        raise SystemExit("No verified image pairs. Use images with more overlap.")
    (i, j), m = max(matches.items(), key=lambda kv: len(kv[1]))
    x1, x2 = kps[i][m[:, 0]].astype(np.float64), kps[j][m[:, 1]].astype(np.float64)
    F = G.eight_point(x1, x2)
    cv2.imwrite(os.path.join(a.out, "matches.jpg"), V.draw_matches(imgs[i], imgs[j], x1, x2))
    cv2.imwrite(os.path.join(a.out, "epipolar.jpg"), V.draw_epipolar_lines(imgs[i], imgs[j], x1, x2, F))

    print("[4/5] Incremental SfM (PnP + triangulation + bundle adjustment)")
    sfm = SfM(K, list(kps), matches, imgs)
    sfm.run()

    print("[5/5] Saving results")
    P, C = sfm.point_cloud()
    centers = np.array([sfm.center(i) for i in sorted(sfm.poses)])
    V.save_ply(os.path.join(a.out, "points.ply"), P, C)
    V.plot_reconstruction(os.path.join(a.out, "reconstruction.png"), P, C, centers)
    errs = [G.reproj_error(K, *sfm.poses[im], sfm.points[p][None], sfm.kps[im][k][None])[0]
            for p in sfm.points for im, k in sfm.obs[p].items()]
    V.plot_error_hist(os.path.join(a.out, "reproj_hist.png"), errs)
    np.savez(os.path.join(a.out, "model.npz"), K=K, points=P, names=np.array(names),
             reg_ids=np.array(sorted(sfm.poses)), centers=centers,
             R=np.array([sfm.poses[i][0] for i in sorted(sfm.poses)]),
             t=np.array([sfm.poses[i][1] for i in sorted(sfm.poses)]))
    print(f"\nRegistered {len(sfm.poses)}/{len(imgs)} images, {len(P)} 3D points, "
          f"mean reprojection error {np.mean(errs):.2f}px, time {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
