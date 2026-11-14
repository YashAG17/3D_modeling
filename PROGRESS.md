# PROGRESS (overwrite this file, do not append)
- Last updated: 2026-11-14 by Codex
- Current task: T-012/T-013 remain in progress; both South Building benchmark attempts are recorded.
- Just completed: Added a COLMAP reference visualization for South Building, rendered from the supplied COLMAP sparse points and camera poses, alongside the three MeshLab screenshots in `results/figures/south-building-meshlab/`. Linked and described it in `RESULTS.md`; the display excludes points outside per-axis 2nd–98th percentiles.
- State of the code: No pipeline source changed. Geometry checks, scoped Pyflakes, and `git diff --check` passed for the reference figure.
- Known issues / gotchas:
  - South Building attempt 2 registered 24/32 images; its comparison covers 24 shared cameras. COLMAP is a reference model, not laser ground truth.
  - The system Python lacks OpenCV; the existing `.venv` has the required dependencies.
- Exact next step: T-012 - capture a 15-30 photo scene dataset with the same camera and no zoom; keep photos out of version control, then run the pipeline and record its measured results.
