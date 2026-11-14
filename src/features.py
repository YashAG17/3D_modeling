"""Unit 3 (3.1 Harris, 3.2 DoG, 3.3 SIFT): feature detection.
Harris and DoG are implemented from scratch (for demonstration / viva);
the full SIFT pipeline uses OpenCV for speed."""
import cv2
import numpy as np
from scipy.ndimage import maximum_filter, minimum_filter


def extract_sift(gray, n_features=8000):
    """SIFT keypoints + RootSIFT descriptors (L1-normalise then sqrt -> better matching)."""
    sift = cv2.SIFT_create(nfeatures=n_features)
    kps, desc = sift.detectAndCompute(gray, None)
    if desc is None or len(kps) == 0:
        return np.zeros((0, 2), np.float32), np.zeros((0, 128), np.float32)
    pts = np.array([k.pt for k in kps], np.float32)
    desc = desc / (desc.sum(axis=1, keepdims=True) + 1e-7)
    return pts, np.sqrt(desc).astype(np.float32)


# ---------- Harris corner detector (from scratch) ----------
def harris_response(gray, k=0.04, sigma=1.5):
    """R = det(M) - k*trace(M)^2, M = Gaussian-weighted structure tensor."""
    g = gray.astype(np.float32) / 255.0
    Ix = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    Iy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    Ixx = cv2.GaussianBlur(Ix * Ix, (0, 0), sigma)
    Iyy = cv2.GaussianBlur(Iy * Iy, (0, 0), sigma)
    Ixy = cv2.GaussianBlur(Ix * Iy, (0, 0), sigma)
    det = Ixx * Iyy - Ixy ** 2
    tr = Ixx + Iyy
    return det - k * tr ** 2


def harris_corners(gray, rel_thresh=0.01, nms_size=7):
    R = harris_response(gray)
    local_max = cv2.dilate(R, np.ones((nms_size, nms_size), np.uint8))
    mask = (R == local_max) & (R > rel_thresh * R.max())
    ys, xs = np.nonzero(mask)
    return np.c_[xs, ys].astype(np.float32)


# ---------- Difference of Gaussians (from scratch) ----------
def dog_pyramid(gray, octaves=4, s=3, sigma0=1.6):
    """Returns list (per octave) of DoG images. k = 2^(1/s), s+3 Gaussians -> s+2 DoGs."""
    img = gray.astype(np.float32) / 255.0
    k = 2 ** (1.0 / s)
    pyramid = []
    for _ in range(octaves):
        gauss = [cv2.GaussianBlur(img, (0, 0), sigma0 * k ** i) for i in range(s + 3)]
        pyramid.append([gauss[i + 1] - gauss[i] for i in range(s + 2)])
        img = gauss[s][::2, ::2]  # next octave: downsample by 2
    return pyramid


def dog_keypoints(pyramid, contrast=0.03, sigma0=1.6, s=3):
    """3x3x3 scale-space extrema of the DoG pyramid -> (x, y, sigma) rows."""
    out = []
    for o, dogs in enumerate(pyramid):
        D = np.stack(dogs)
        ext = ((D == maximum_filter(D, size=3)) | (D == minimum_filter(D, size=3)))
        ext &= np.abs(D) > contrast
        ext[0] = False
        ext[-1] = False
        sc, ys, xs = np.nonzero(ext)
        for a, y, x in zip(sc, ys, xs):
            out.append((x * 2 ** o, y * 2 ** o, sigma0 * 2 ** (o + a / s)))
    return np.array(out, np.float32).reshape(-1, 3)
