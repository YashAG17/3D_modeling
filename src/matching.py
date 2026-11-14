"""Unit 3 (3.4 Feature matching, 3.5 RANSAC): descriptor matching + geometric verification."""
import itertools
import cv2
import numpy as np
from . import geometry as G


def match_descriptors(d1, d2, ratio=0.8):
    """Lowe ratio test + mutual nearest-neighbour check. Returns (M,2) index pairs."""
    if len(d1) < 8 or len(d2) < 8:
        return np.zeros((0, 2), int)
    bf = cv2.BFMatcher(cv2.NORM_L2)
    fwd = {}
    for pair in bf.knnMatch(d1, d2, k=2):
        if len(pair) == 2 and pair[0].distance < ratio * pair[1].distance:
            fwd[pair[0].queryIdx] = pair[0].trainIdx
    back = {m[0].queryIdx: m[0].trainIdx for m in bf.knnMatch(d2, d1, k=1) if len(m) == 1}
    out = [(q, t) for q, t in fwd.items() if back.get(t) == q]
    return np.array(out, int).reshape(-1, 2)


def match_all_pairs(kps, descs, ransac_thresh=1.0, min_inliers=30, use_opencv=False, window=None):
    """Match every image pair, keep only epipolar-consistent (RANSAC) matches.
    window=k -> only match images whose index differs by <= k (for video-like sequences)."""
    n = len(kps)
    matches = {}
    for i, j in itertools.combinations(range(n), 2):
        if window and abs(i - j) > window:
            continue
        m = match_descriptors(descs[i], descs[j])
        if len(m) < min_inliers:
            continue
        x1, x2 = kps[i][m[:, 0]].astype(np.float64), kps[j][m[:, 1]].astype(np.float64)
        if use_opencv:
            _, mask = cv2.findFundamentalMat(x1, x2, cv2.FM_RANSAC, ransac_thresh, 0.999)
            inl = np.zeros(len(m), bool) if mask is None else mask.ravel().astype(bool)
        else:
            _, inl = G.ransac_fundamental(x1, x2, thresh=ransac_thresh)
        print(f"  pair ({i},{j}): {len(m)} putative -> {inl.sum()} inliers")
        if inl.sum() >= min_inliers:
            matches[(i, j)] = m[inl]
    return matches
