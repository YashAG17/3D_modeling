# PROGRESS (overwrite this file, do not append)
- Last updated: 2026-11-14 by Codex
- Current task: T-012/T-013 remain in progress; both South Building benchmark attempts are recorded.
- Just completed: Removed the unused `views.py` utility, which only read and wrote hard-coded `output3/` paths and had no references elsewhere. Kept `flatness.py` because it can reproduce the flatness metric documented in `RESULTS.md`.
- State of the code: The core pipeline and analysis scripts remain in place. No photos or generated output directories were changed.
- Known issues / gotchas:
  - South Building attempt 2 registered 24/32 images; its comparison covers 24 shared cameras. COLMAP is a reference model, not laser ground truth.
  - The system Python lacks OpenCV; the existing `.venv` has the required dependencies.
- Exact next step: T-012 - capture a 15-30 photo scene dataset with the same camera and no zoom; keep photos out of version control, then run the pipeline and record its measured results.
