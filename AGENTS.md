# AGENTS.md
## Project summary
Mini-SfM: a Python Structure-from-Motion pipeline (features -> matching -> epipolar geometry -> incremental
reconstruction -> bundle adjustment) producing camera poses and a sparse 3D point cloud from multiple photos.
College project (LNMIIT Computer Vision). Full spec: PRD.md. Reference system: COLMAP (baseline only).

## Stack (do not change versions or add major dependencies without logging a decision)
Python 3.10+, NumPy 2.x, SciPy 1.x, opencv-python (tested 5.0.0), Matplotlib. pytest for tests (after T-011).

## Commands
- Install: `pip install -r requirements.txt`
- Run: `python run_pipeline.py --images images --out output --demos`
- Fast mode (OpenCV RANSAC): add `--fast`
- Test: `python -m tests.test_geometry` (or `pytest` after T-011)
- Synthetic scene: `python -m tests.make_synthetic_scene --out images_synth`
- Compare with COLMAP: `python evaluate_vs_colmap.py --colmap_txt <ws/txt/images.txt>`
- Lint: `python -m pyflakes .` (install pyflakes if missing)

## Folder structure
src/camera.py (K, loading) | features.py (SIFT, Harris, DoG) | geometry.py (8-point, RANSAC, E, triangulation)
| matching.py | sfm.py (incremental SfM) | bundle_adjustment.py | visualize.py ; tests/ ; run_pipeline.py

## Conventions
- Poses are world->camera: x_cam = R X + t. Camera centre C = -R^T t.
- Image points are pixel coordinates (N,2); use `to_normalized` for normalised coordinates.
- `matches[(i, j)]` always has i < j; use `SfM.get_matches(i, j)` to read either orientation.
- Functions are pure NumPy where possible; docstring says which course unit they belong to.
- Do not commit photos, `output/`, or `.env`.

## On session start (always)
1. Read PROGRESS.md, then TASKS.md, then run `git log --oneline -15`.
2. Read DECISIONS.md entries relevant to the area you're working on.
3. Read PRD.md sections only as needed.
4. Pick up the task marked [~], or else the first [ ] task. Work on ONE task at a time.

## Rules
- Never reverse or contradict a decision in DECISIONS.md. If you think it's wrong,
  stop and tell the user why. Don't change it yourself.
- Don't rewrite or refactor code outside your current task.
- Don't remove or weaken tests to make them pass.
- Never put secrets or API keys in code or docs. Use .env and keep .env.example
  updated.
- If you're unsure about a requirement, ask the user. Don't guess.

## After EACH completed task (do this right away, not at the end of the session)
1. Run the tests and the linter. Fix failures before marking the task done.
2. Update TASKS.md (mark [x], or [!] with a reason).
3. OVERWRITE PROGRESS.md using its template: current state, what was just done,
   known issues, the exact next step.
4. If you made a significant design choice (library, architecture, data shape,
   API contract, tradeoff), append it to DECISIONS.md. Don't log routine actions.
5. Commit: `git add -A && git commit -m "T-XXX: <what changed>"`

## If you are about to run out of context or hit a limit
Stop coding right away and update PROGRESS.md with exactly where you stopped,
including half-finished work and files touched.

## Project-specific cautions
- Numbers in slides/RESULTS.md must come from actual runs; never invent results.
- Course alignment: from-scratch parts map to Units 1, 3, 5 (see README table). Keep docstrings' unit tags.
