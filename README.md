# Mini-SfM: 3D Reconstruction from Multiple Images (Python)
LNMIIT CCE - Computer Vision project. Team: Parkhi Agarwal (24UEC204), Yash Agarwal (24UCC189)

## Setup & run
    pip install -r requirements.txt
    # put 15-30 photos of ONE static, textured object/scene in images/
    python -m tests.test_geometry                      # sanity test on synthetic data (no photos needed)
    python -m tests.make_synthetic_scene --out images_synth   # ground-truth test scene (optional)
    python run_pipeline.py --images images --out output --demos
    # options: --focal <pixels>  --fast (OpenCV RANSAC)  --window 3 (match only neighbours)  --max_size 1200

Outputs in `output/`: `points.ply` (open in MeshLab / CloudCompare), `reconstruction.png`,
`matches.jpg`, `epipolar.jpg`, `reproj_hist.png`, `model.npz`, `demo_harris.jpg`, `demo_dog.jpg`.

## Files
| File | What it does | Syllabus |
|---|---|---|
| src/camera.py | image loading, pinhole intrinsics K, normalised coords | Unit 1: 1.2, 1.3 |
| src/features.py | SIFT (OpenCV) + **Harris & DoG from scratch** | Unit 3: 3.1, 3.2, 3.3 |
| src/matching.py | ratio test + mutual check + RANSAC verification | Unit 3: 3.4, 3.5 |
| src/geometry.py | **from scratch**: Rodrigues, normalised 8-point, RANSAC for F, Sampson error, E decomposition, cheirality, DLT triangulation | Unit 5: 5.1, 5.3; Unit 3: 3.5 |
| src/sfm.py | incremental SfM: initial pair, PnP registration, track growth, pruning | Unit 5: 5.4 |
| src/bundle_adjustment.py | sparse non-linear least-squares refinement | Unit 5: 5.4 (extension) |
| src/visualize.py | PLY export, 3D plot, epipolar lines, match drawing | Unit 5: 5.1 |
| run_pipeline.py | runs everything end to end | - |
| evaluate_vs_colmap.py | compares camera centres with COLMAP (Umeyama alignment) | validation |
| tests/ | synthetic tests with known ground truth | - |

## What is from scratch vs library
From scratch: Harris, DoG, 8-point, RANSAC, Sampson error, E decomposition, triangulation, incremental SfM logic,
bundle-adjustment residuals. Library: SIFT (cv2), brute-force NN search (cv2), PnP-RANSAC (cv2.solvePnPRansac),
optimiser (scipy.optimize.least_squares).

## Capture tips
Same camera, no zoom change, 60-80% overlap between consecutive photos, move around the object (do not only rotate
in place), textured surfaces, avoid glass/mirrors/moving objects. Pass `--focal` if you know it
(focal_px = focal_mm / sensor_width_mm * image_width_px) - otherwise f = 1.2 * max(w, h) is assumed.

## Limitations (mention in the viva)
Sparse reconstruction only (no dense MVS); intrinsics fixed (no self-calibration); no loop closure / global BA
beyond the incremental one; scale is arbitrary (monocular SfM); exhaustive matching is O(n^2).
