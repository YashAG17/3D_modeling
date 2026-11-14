import sys
import numpy as np

# 1. Load the 3D points saved by the pipeline (model.npz)
P = np.load(sys.argv[1])["points"]

# 2. Throw away the 2% most extreme points on each axis (stray points far away)
lo, hi = np.percentile(P, 2, 0), np.percentile(P, 98, 0)
P = P[((P >= lo) & (P <= hi)).all(1)]

# 3. Fit a plane, ignoring points that are far from it, and repeat 10 times
c = P.mean(0)                                # a point on the plane (the centre)
for _ in range(10):
    n = np.linalg.svd(P - c)[2][2]           # direction perpendicular to the plane
    d = (P - c) @ n                          # each point's distance from the plane
    s = 1.4826 * np.median(np.abs(d - np.median(d)))   # typical spread of distances
    m = np.abs(d - np.median(d)) < 3 * s     # keep only points close to the plane
    c = P[m].mean(0)                         # re-centre using just those points
    n = np.linalg.svd(P[m] - c)[2][2]        # re-fit the plane direction

# 4. Final distances of all points to the plane
d = (P - c) @ n

# 5. Scene size = the diagonal of the box that contains the points
ext = np.linalg.norm(P.max(0) - P.min(0))

# 6. Typical distance from the plane, as a percentage of scene size
print(f"plane RMS = {100 * np.sqrt((d**2).mean()) / ext:.2f}% of scene extent")