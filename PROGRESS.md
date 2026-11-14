# PROGRESS (overwrite this file, do not append)
- Last updated: 2026-11-14 by Claude Sonnet 5.5
- Current task: none in progress. Milestone 1 (T-001..T-010) complete.
- Just completed: full pipeline + synthetic tests. Synthetic 7-image room: 7/7 registered, 0.05 px mean
  reprojection error, camera-centre RMSE 0.0009 (about 0.04% of the 2.4 span) in both own-RANSAC and `--fast` modes.
- State of the code: WORKS on synthetic data. NOT yet run on real photos. No git repo initialised yet.
  Tests are plain-assert scripts (`python -m tests.test_geometry`), not pytest.
- Known issues / gotchas:
  - Real-photo behaviour untested: focal length is guessed (1.2 x max side) unless `--focal` is given.
  - Own RANSAC is slower than `--fast` (about 9 s vs 6 s on 7 small images; grows quickly with image count).
  - Exhaustive matching is O(n^2) pairs; use `--window` for sequences.
  - Bundle adjustment needs the two-stage (linear then Huber) solve; do not switch back to Huber-only (D-007).
- Exact next step: T-011 - `git init`, add the remote https://github.com/YashAG17/3D_modeling (currently empty),
  push, then convert tests/test_geometry.py to pytest.
