"""Unit 1 (1.2 Image formation & digital camera, 1.3 Geometric primitives):
pinhole camera model, intrinsics matrix K, image loading."""
import os
import cv2
import numpy as np

IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")


def load_images(folder, max_size=1600):
    """Load all images (sorted by name), downscale so the longer side <= max_size."""
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(IMG_EXT))
    if len(files) < 3:
        raise ValueError(f"Need at least 3 images in {folder}, found {len(files)}")
    imgs = []
    for f in files:
        im = cv2.imread(os.path.join(folder, f))
        h, w = im.shape[:2]
        s = max_size / max(h, w)
        if s < 1:
            im = cv2.resize(im, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        imgs.append(im)
    return files, imgs


def default_intrinsics(width, height, focal_px=None, f_factor=1.2):
    """K = [[f,0,cx],[0,f,cy],[0,0,1]]. If focal is unknown, guess f = 1.2*max(w,h)
    (typical for phone cameras). Square pixels, principal point at image centre."""
    f = focal_px if focal_px else f_factor * max(width, height)
    return np.array([[f, 0, width / 2.0],
                     [0, f, height / 2.0],
                     [0, 0, 1.0]])


def to_normalized(K, x):
    """Pixel coords (N,2) -> normalized camera coords (N,2): K^-1 [u v 1]^T."""
    xh = np.c_[x, np.ones(len(x))]
    return (np.linalg.inv(K) @ xh.T).T[:, :2]
