import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# read points.ply (ascii: 10 header lines, then x y z r g b)
rows = []
with open("output3/points.ply") as f:
    started = False
    for line in f:
        if started:
            rows.append(line.split())
        elif line.startswith("end_header"):
            started = True
data = np.array(rows, dtype=float)
pts, cols = data[:, :3], data[:, 3:6] / 255.0

# drop far-away stray points
lo, hi = np.percentile(pts, 2, axis=0), np.percentile(pts, 98, axis=0)
keep = ((pts >= lo) & (pts <= hi)).all(axis=1)
pts, cols = pts[keep], cols[keep]

views = [("front", -70, -90), ("top", -150, -90), ("side", -70, 0), ("oblique", -45, -45)]
fig = plt.figure(figsize=(12, 10))
for i, (name, elev, azim) in enumerate(views, 1):
    ax = fig.add_subplot(2, 2, i, projection="3d")
    ax.scatter(*pts.T, c=cols, s=2)
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(name)
fig.savefig("output3/views.png", dpi=120, bbox_inches="tight")
print("saved output3/views.png")