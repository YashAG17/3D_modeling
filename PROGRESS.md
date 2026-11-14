# PROGRESS (overwrite this file, do not append)
- Last updated: 2026-11-14 by Codex
- Current task: T-012/T-013 remain in progress; both South Building benchmark attempts are recorded.
- Just completed: Added three user-provided MeshLab views of `out_f1064/points.ply` under `results/figures/desk-f1064-meshlab/` and embedded them in the desk results section of `RESULTS.md`.
- State of the code: No pipeline source changed. Screenshots are retained in uploaded formats (one WebP and two PNG). Geometry checks, scoped Pyflakes, and `git diff --check` passed.
- Known issues / gotchas:
  - South Building attempt 2 registered 24/32 images; its comparison covers 24 shared cameras. COLMAP is a reference model, not laser ground truth.
  - The system Python lacks OpenCV; the existing `.venv` has the required dependencies.
- Exact next step: T-012 - capture a 15-30 photo scene dataset with the same camera and no zoom; keep photos out of version control, then run the pipeline and record its measured results.
