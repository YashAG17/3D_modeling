# DECISIONS
Append-only log of SIGNIFICANT decisions only. Older entries may later be condensed into a summary here.

## D-001 · 2026-11-14 · Python with NumPy/SciPy/OpenCV
Why: course is Python-based; fast to iterate; OpenCV supplies SIFT/PnP. Rejected: C++ (slower to write and explain), pycolmap wrapper (not "from scratch"). Affects: whole repo.

## D-002 · 2026-11-14 · Incremental SfM (not global SfM)
Why: simpler to implement and explain; same family as COLMAP. Rejected: global rotation averaging (more complex). Affects: src/sfm.py.

## D-003 · 2026-11-14 · From-scratch vs library boundary
Why: grade rewards understanding. From scratch: Harris, DoG, 8-point, RANSAC, Sampson, E decomposition, DLT triangulation, SfM logic, BA residuals. Library: SIFT, BF matcher, PnP-RANSAC, scipy optimiser. Rejected: writing SIFT/PnP ourselves (time, little extra learning). Affects: src/*.

## D-004 · 2026-11-14 · Fixed intrinsics, guessed focal = 1.2 x max(w,h) unless --focal
Why: avoids self-calibration complexity. Rejected: EXIF parsing (extra dependency), BA focal refinement (later option). Affects: src/camera.py, run_pipeline.py.

## D-005 · 2026-11-14 · RootSIFT descriptors
Why: better matching than raw SIFT at no cost. Rejected: raw SIFT. Affects: src/features.py.

## D-006 · 2026-11-14 · Pose convention world->camera; E derived from RANSAC-verified F
Why: matches OpenCV/COLMAP convention, easy to compare. Rejected: camera->world storage. Affects: sfm.py, evaluate_vs_colmap.py.

## D-007 · 2026-11-14 · Bundle adjustment in two stages (linear loss, then Huber)
Why: Huber-only from a rough start stalled at about 7.6 px with the sparse LSMR solver on synthetic data; two-stage reaches 0.09 px. Rejected: Huber-only, dense solver (does not scale). Affects: src/bundle_adjustment.py.

## D-008 · 2026-11-14 · Initial pair chosen by number of reliably triangulated points among top-20 pairs
Why: highest-inlier pair can have tiny baseline and a bad pose (own-RANSAC run gave 0.21 camera RMSE; now 0.0009). Rejected: most-inliers pair. Affects: src/sfm.py initialize().

## D-009 · 2026-11-14 · COLMAP is a validation baseline only, never a dependency of the pipeline
Why: project must be our own implementation. Rejected: calling pycolmap inside the pipeline. Affects: evaluate_vs_colmap.py.

## D-010 · 2026-11-14 · Sparse reconstruction only (no dense MVS)
Why: time; syllabus covers epipolar geometry, triangulation, SfM. Rejected: PatchMatch MVS. Affects: scope in PRD.

## D-011 · 2026-11-14 · Lower thresholds for real photos
Why: real desk photos have low texture, so min matches per pair and min initial-pair points were lowered from 50 to 30, and SIFT contrastThreshold from the default 0.04 to 0.01, to get more features and matches. Trade-off: more noisy matches and slower runs (195 s on 19 photos). Rejected: keeping the defaults. Affects: src/sfm.py, src/features.py.