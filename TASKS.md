# TASKS
Markers: [ ] todo, [~] in progress, [x] done, [!] blocked (with reason)
Format: `- [ ] T-001: <task> - Done when: <check>`

## Milestone 1 - Core pipeline (DONE)
- [x] T-001: Project skeleton, requirements.txt, folders - Done when: `python -c "import src"` works
- [x] T-002: `src/camera.py` image loading + intrinsics - Done when: K printed correctly by run_pipeline
- [x] T-003: `src/features.py` RootSIFT + Harris + DoG - Done when: `--demos` writes demo_harris.jpg / demo_dog.jpg
- [x] T-004: `src/geometry.py` 8-point, RANSAC, E decomposition, DLT triangulation - Done when: tests/test_geometry.py passes
- [x] T-005: `src/matching.py` ratio+mutual+RANSAC verification - Done when: inlier counts printed per pair
- [x] T-006: `src/bundle_adjustment.py` - Done when: synthetic BA residual 11 px -> <1 px
- [x] T-007: `src/sfm.py` incremental SfM - Done when: 7/7 synthetic images registered
- [x] T-008: `src/visualize.py` + `run_pipeline.py` - Done when: all output files are written
- [x] T-009: Synthetic tests + scene generator - Done when: "ALL TESTS PASSED"
- [x] T-010: `evaluate_vs_colmap.py` (Umeyama alignment) - Done when: runs on synthetic ground truth, RMSE ~0.001

## Milestone 2 - Repo, real data, validation
- [x] T-011: git init, push to github.com/YashAG17/3D_modeling, convert tests to pytest - Done when: `pytest` passes and repo shows files on GitHub
- [~] T-012: Capture 2 real datasets (15-30 photos each; one object, one scene), same camera, no zoom - Current: 19 desk photos captured; scene dataset pending. Photos are in ignored `images/`.
- [~] T-013: Run pipeline on real data, record numbers (images registered, #points, mean reproj error, runtime) in RESULTS.md - Current: desk dataset results recorded; second dataset pending.
- [x] T-014: Run COLMAP on the same photos, run evaluate_vs_colmap.py - Done when: RMSE % of scene extent is in RESULTS.md
- [ ] T-015: Ablation: own RANSAC vs `--fast`; with vs without bundle adjustment - Done when: table in RESULTS.md
- [ ] T-016: Fix failures found on real data (thresholds, focal guess, matching window) - Done when: >= 80% images register on both datasets; each change logged in DECISIONS.md

## Milestone 3 - Presentation and viva (10 slides: 1 motivation, 2 literature, 6 methodology, 1 result)
- [ ] T-017: Literature slides content: COLMAP repo + Schonberger & Frahm CVPR 2016 + Szeliski ch. on SfM; "what they did / what we add" - Done when: 2 slides drafted
- [ ] T-018: Methodology slide plan (6 slides): features, matching+RANSAC, epipolar geometry, pose+triangulation, PnP+incremental, bundle adjustment - Done when: outline + figure per slide
- [ ] T-019: Build the 10-slide PPT using real output figures - Done when: deck is exported and reviewed
- [ ] T-020: Viva Q&A sheet (20 questions) + demo rehearsal - Done when: both members can explain every file in `src/`

## Optional (only if time remains)
- [ ] T-021: Learned matcher extension (Siamese network, course Lab 8) - Done when: matching accuracy compared with SIFT on one pair
