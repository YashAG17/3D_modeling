# PRD - Mini-SfM: 3D Reconstruction from Multiple Images
Course: Computer Vision (BTech CCE, LNMIIT). Team: Parkhi Agarwal (24UEC204), Yash Agarwal (24UCC189).

## Overview
Given 15-30 photos of a static scene taken with one camera, recover (a) the camera pose of every photo and
(b) a sparse 3D point cloud, using a Python pipeline built mostly from scratch. COLMAP is the reference
system (github.com/colmap/colmap); we compare against it but do not depend on it.

## Goals
- Working end-to-end Structure-from-Motion pipeline in Python, runnable with one command.
- Core geometry written from scratch (Harris, DoG, 8-point, RANSAC, triangulation, SfM logic).
- Quantitative validation: synthetic ground truth + comparison against COLMAP on a real dataset.
- Course deliverable: 10-slide PPT + code + viva. Marks: Motivation 5, PPT 5, Code 5, Viva 5.

## Non-goals
Dense reconstruction / meshing, real-time operation, GUI, self-calibration, loop closure, GPU code.

## Core flows
1. User puts photos in `images/` -> runs `python run_pipeline.py` -> gets `output/points.ply` + diagnostics.
2. Developer runs `python -m tests.test_geometry` (or pytest) to verify the maths on synthetic data.
3. User runs COLMAP on the same photos and `evaluate_vs_colmap.py` to get camera-centre RMSE.

## v1 features and acceptance criteria
| Feature | Acceptance criteria |
|---|---|
| Feature extraction | SIFT (RootSIFT) per image; Harris + DoG demos saved with `--demos` |
| Matching + verification | Ratio test + mutual check + own RANSAC (8-point) for F; inlier counts printed per pair |
| Initial pair + pose | E from F, 4-way decomposition, cheirality check; best pair by # reliable triangulated points |
| Incremental SfM | Registers new images via PnP-RANSAC, triangulates new points, prunes outliers |
| Bundle adjustment | Mean reprojection error drops after BA on synthetic test (<1 px) |
| Outputs | `points.ply`, `reconstruction.png`, `epipolar.jpg`, `matches.jpg`, `reproj_hist.png`, `model.npz` |
| Validation | Synthetic scene: camera-centre RMSE < 1% of camera span. Real scene: >= 80% images registered, mean reprojection error < 1.5 px |
| COLMAP comparison | `evaluate_vs_colmap.py` prints Sim(3)-aligned camera-centre RMSE |

## Data model (in memory, `src/sfm.py`)
- `poses[img] = (R, t)` world->camera (x_cam = R X + t)
- `points[pid] = xyz`; `obs[pid] = {img: keypoint_idx}` (a track); `kp2pid[img][keypoint_idx] = pid`
- `matches[(i, j)] = array (M,2)` of verified keypoint index pairs, with i < j

## Tech stack
- Python 3.10+ - language
- NumPy 2.x - from-scratch linear algebra
- SciPy 1.x - sparse least squares (bundle adjustment), image filters
- OpenCV (opencv-python) - SIFT, brute-force matcher, PnP-RANSAC. Tested with OpenCV 5.0.0, NumPy 2.5.4, SciPy 1.18.1
- Matplotlib - plots (Agg backend)
- COLMAP (external binary, optional) - baseline for validation only

## Folder structure
    mini_sfm/
      PRD.md AGENTS.md TASKS.md PROGRESS.md DECISIONS.md RESULTS.md(later) README.md
      requirements.txt run_pipeline.py evaluate_vs_colmap.py
      src/{camera,features,geometry,matching,sfm,bundle_adjustment,visualize}.py
      tests/{test_geometry.py, make_synthetic_scene.py}
      images/ (user photos, git-ignored)  output/ (generated, git-ignored)

## Testing approach
Synthetic data with known ground truth (no photos needed): RANSAC, pose recovery, triangulation, bundle
adjustment (`tests/test_geometry.py`); a ray-cast textured room (`tests/make_synthetic_scene.py`) for the full
pipeline. Plain asserts today; migrate to pytest (T-011).

## Out of scope / future ideas
Dense MVS, meshing, learned matchers (Siamese network, course Lab 8), intrinsics refinement in BA,
vocabulary-tree matching for large image sets.
