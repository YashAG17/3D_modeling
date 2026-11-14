"""Unit 5 (5.1-5.4): Incremental Structure-from-Motion (the 'mini-COLMAP' core).

Pipeline:  verified matches -> pick initial pair -> E -> (R,t) -> triangulate
           -> loop { PnP-register next image -> triangulate new points -> bundle adjust -> prune }
Poses are stored world->camera:  x_cam = R X + t.
"""
from collections import defaultdict
import cv2
import numpy as np
from . import geometry as G
from .camera import to_normalized
from .bundle_adjustment import bundle_adjust


class SfM:
    def __init__(self, K, kps, matches, images, reproj_thresh=4.0, min_angle=1.5):
        self.K, self.kps, self.matches, self.images = K, kps, matches, images
        self.thr, self.min_angle = reproj_thresh, min_angle
        self.poses = {}                       # img -> (R, t)
        self.points = {}                      # pid -> xyz
        self.obs = defaultdict(dict)          # pid -> {img: keypoint idx}
        self.kp2pid = [dict() for _ in kps]   # per image: keypoint idx -> pid
        self.next_pid = 0

    # ---------- helpers ----------
    def P(self, i):
        R, t = self.poses[i]
        return self.K @ np.hstack([R, t.reshape(3, 1)])

    def center(self, i):
        R, t = self.poses[i]
        return -R.T @ t

    def get_matches(self, i, j):
        """Return (ki, kj) keypoint-index arrays for images i and j."""
        if (i, j) in self.matches:
            m = self.matches[(i, j)]
            return m[:, 0], m[:, 1]
        if (j, i) in self.matches:
            m = self.matches[(j, i)]
            return m[:, 1], m[:, 0]
        return np.zeros(0, int), np.zeros(0, int)

    def _add_point(self, X, observations):
        pid = self.next_pid
        self.next_pid += 1
        self.points[pid] = X
        for img, k in observations.items():
            self.obs[pid][img] = k
            self.kp2pid[img][k] = pid

    def _triangulate_pair(self, i, j, ki, kj):
        Ri, ti = self.poses[i]
        Rj, tj = self.poses[j]
        xi, xj = self.kps[i][ki].astype(np.float64), self.kps[j][kj].astype(np.float64)
        X = G.triangulate_dlt(self.P(i), self.P(j), xi, xj)
        ok = np.isfinite(X).all(axis=1)
        X = np.nan_to_num(X)
        zi, zj = (Ri @ X.T).T[:, 2] + ti[2], (Rj @ X.T).T[:, 2] + tj[2]
        ok &= (zi > 0) & (zj > 0)
        with np.errstate(invalid="ignore"):
            ok &= (G.reproj_error(self.K, Ri, ti, X, xi) < self.thr)
            ok &= (G.reproj_error(self.K, Rj, tj, X, xj) < self.thr)
        ok &= G.triangulation_angle(X, self.center(i), self.center(j)) > self.min_angle
        return X, ok

    # ---------- step 1: initial pair ----------
    def initialize(self, n_candidates=20):
        """Try the pairs with most inliers; keep the one that triangulates the most
        well-conditioned points (small-baseline pairs give weak poses, so inlier count alone
        is not enough - same idea as COLMAP's initial-pair selection)."""
        pairs = sorted(self.matches, key=lambda p: -len(self.matches[p]))[:n_candidates]
        best = None
        for i, j in pairs:
            m = self.matches[(i, j)]
            if len(m) < 50:
                continue
            x1, x2 = self.kps[i][m[:, 0]].astype(np.float64), self.kps[j][m[:, 1]].astype(np.float64)
            F = G.eight_point(x1, x2)
            E = G.essential_from_F(F, self.K, self.K)
            R, t, _ = G.recover_pose(E, to_normalized(self.K, x1), to_normalized(self.K, x2))
            self.poses = {i: (np.eye(3), np.zeros(3)), j: (R, t / np.linalg.norm(t))}
            X, ok = self._triangulate_pair(i, j, m[:, 0], m[:, 1])
            if best is None or ok.sum() > best[0]:
                best = (int(ok.sum()), i, j, R, t / np.linalg.norm(t), X, ok, m)
        self.poses = {}
        if best is None or best[0] < 50:
            return False
        n_ok, i, j, R, t, X, ok, m = best
        self.poses = {i: (np.eye(3), np.zeros(3)), j: (R, t)}
        for x, a, b in zip(X[ok], m[ok, 0], m[ok, 1]):
            self._add_point(x, {i: int(a), j: int(b)})
        print(f"Initial pair ({i},{j}): {n_ok} 3D points")
        return True

    # ---------- step 2: register new image with PnP ----------
    def _2d3d(self, i):
        corr = {}
        for r in self.poses:
            kr, ki = self.get_matches(r, i)
            for a, b in zip(kr, ki):
                pid = self.kp2pid[r].get(int(a))
                if pid is not None and int(b) not in corr:
                    corr[int(b)] = pid
        return corr

    def register(self, i):
        corr = self._2d3d(i)
        if len(corr) < 12:
            return False
        kis = list(corr)
        pids = [corr[k] for k in kis]
        obj = np.array([self.points[p] for p in pids], np.float64)
        img = self.kps[i][kis].astype(np.float64)
        ok, rvec, tvec, inl = cv2.solvePnPRansac(
            obj, img, self.K, None, iterationsCount=2000, reprojectionError=self.thr,
            confidence=0.999, flags=cv2.SOLVEPNP_EPNP)
        if not ok or inl is None or len(inl) < 12:
            return False
        inl = inl.ravel()
        rvec, tvec = cv2.solvePnPRefineLM(obj[inl], img[inl], self.K, None, rvec, tvec)
        self.poses[i] = (cv2.Rodrigues(rvec)[0], tvec.ravel())
        for n in inl:
            pid, k = pids[n], kis[n]
            if i not in self.obs[pid]:
                self.obs[pid][i] = k
                self.kp2pid[i][k] = pid
        print(f"Registered image {i}: PnP inliers {len(inl)}/{len(kis)}")
        return True

    # ---------- step 3: grow the map ----------
    def expand(self, i):
        new = 0
        for r in list(self.poses):
            if r == i:
                continue
            kr, ki = self.get_matches(r, i)
            cand_r, cand_i = [], []
            for a, b in zip(kr, ki):
                a, b = int(a), int(b)
                pr, pi = self.kp2pid[r].get(a), self.kp2pid[i].get(b)
                if pr is None and pi is None:
                    cand_r.append(a); cand_i.append(b)
                elif pr is not None and pi is None and i not in self.obs[pr]:
                    self.obs[pr][i] = b; self.kp2pid[i][b] = pr          # extend track
                elif pi is not None and pr is None and r not in self.obs[pi]:
                    self.obs[pi][r] = a; self.kp2pid[r][a] = pi          # extend track
            if cand_r:
                cr, ci = np.array(cand_r), np.array(cand_i)
                X, ok = self._triangulate_pair(r, i, cr, ci)
                for x, a, b in zip(X[ok], cr[ok], ci[ok]):
                    if a not in self.kp2pid[r] and b not in self.kp2pid[i]:
                        self._add_point(x, {r: int(a), i: int(b)})
                        new += 1
        print(f"  +{new} new points (total {len(self.points)})")

    # ---------- step 4: bundle adjustment + pruning ----------
    def run_ba(self, max_nfev=30):
        img_ids, pids = sorted(self.poses), sorted(self.points)
        cidx = {im: n for n, im in enumerate(img_ids)}
        pidx = {p: n for n, p in enumerate(pids)}
        cams = np.array([np.r_[cv2.Rodrigues(self.poses[im][0])[0].ravel(), self.poses[im][1]]
                         for im in img_ids])
        pts = np.array([self.points[p] for p in pids])
        oc, op, oxy = [], [], []
        for p in pids:
            for im, k in self.obs[p].items():
                oc.append(cidx[im]); op.append(pidx[p]); oxy.append(self.kps[im][k])
        before = self.mean_reproj_error()
        cams, pts = bundle_adjust(self.K, cams, pts, np.array(oc), np.array(op),
                                  np.array(oxy, np.float64), max_nfev=max_nfev)
        for im in img_ids:
            c = cams[cidx[im]]
            self.poses[im] = (cv2.Rodrigues(c[:3])[0], c[3:6].copy())
        for p in pids:
            self.points[p] = pts[pidx[p]]
        print(f"  BA: mean reproj error {before:.2f} -> {self.mean_reproj_error():.2f} px")

    def prune(self):
        """Drop observations with large reprojection error / behind camera; drop weak points."""
        for pid in list(self.points):
            X = self.points[pid][None]
            for img, k in list(self.obs[pid].items()):
                R, t = self.poses[img]
                z = (R @ X.T).T[0, 2] + t[2]
                e = G.reproj_error(self.K, R, t, X, self.kps[img][k][None].astype(np.float64))[0]
                if not (z > 0 and e < self.thr):
                    del self.obs[pid][img]
                    self.kp2pid[img].pop(k, None)
            if len(self.obs[pid]) < 2:
                for img, k in self.obs[pid].items():
                    self.kp2pid[img].pop(k, None)
                del self.points[pid]
                del self.obs[pid]

    # ---------- driver ----------
    def run(self):
        if not self.initialize():
            raise RuntimeError("Could not find a good initial pair (need more overlap / baseline).")
        self.run_ba(); self.prune()
        n = len(self.kps)
        while True:
            unreg = [i for i in range(n) if i not in self.poses]
            if not unreg:
                break
            ranked = sorted(((len(self._2d3d(i)), i) for i in unreg), reverse=True)
            progressed = False
            for cnt, i in ranked:
                if cnt < 12:
                    break
                if self.register(i):
                    self.expand(i); self.run_ba(); self.prune()
                    progressed = True
                    break
            if not progressed:
                print("Stopping: remaining images cannot be registered:", unreg)
                break

    # ---------- outputs ----------
    def mean_reproj_error(self):
        errs = []
        for pid, X in self.points.items():
            for img, k in self.obs[pid].items():
                R, t = self.poses[img]
                errs.append(G.reproj_error(self.K, R, t, X[None], self.kps[img][k][None])[0])
        return float(np.mean(errs)) if errs else float("nan")

    def point_cloud(self):
        """Returns (N,3) points and (N,3) RGB colours sampled from the first observing image."""
        pids = sorted(self.points)
        P = np.array([self.points[p] for p in pids])
        cols = []
        for p in pids:
            img, k = next(iter(self.obs[p].items()))
            x, y = np.round(self.kps[img][k]).astype(int)
            h, w = self.images[img].shape[:2]
            b, g, r = self.images[img][min(y, h - 1), min(x, w - 1)]
            cols.append((r, g, b))
        return P, np.array(cols, np.uint8)
