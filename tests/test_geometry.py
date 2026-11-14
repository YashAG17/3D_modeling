"""Pytest checks for the synthetic geometry and bundle-adjustment pipeline."""

import numpy as np
import pytest

from src import geometry as G
from src.bundle_adjustment import bundle_adjust, residuals


@pytest.fixture
def synthetic_scene():
    """Build the deterministic two-camera scene shared by the tests."""
    rng = np.random.default_rng(1)
    K = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1.0]])
    X = rng.uniform(-1, 1, (300, 3)) + np.array([0, 0, 5])
    R2 = G.rodrigues(np.array([0.02, 0.15, -0.03]))
    t2 = np.array([-1.0, 0.05, 0.1])
    x1 = G.project(K, np.eye(3), np.zeros(3), X) + rng.normal(0, 0.3, (300, 2))
    x2 = G.project(K, R2, t2, X) + rng.normal(0, 0.3, (300, 2))
    bad = rng.choice(300, 60, replace=False)
    x2[bad] += rng.uniform(-80, 80, (60, 2))
    return rng, K, X, R2, t2, x1, x2, bad


def test_ransac_pose_recovery_and_triangulation(synthetic_scene):
    """Check robust epipolar geometry and triangulation on synthetic data."""
    _, K, X, R2, t2, x1, x2, bad = synthetic_scene

    F, inliers = G.ransac_fundamental(x1, x2, thresh=1.5)
    assert inliers.sum() > 200
    assert inliers[bad].sum() < 10

    E = G.essential_from_F(F, K, K)
    xn1, xn2 = (x1 - K[:2, 2]) / 800, (x2 - K[:2, 2]) / 800
    R, t, _ = G.recover_pose(E, xn1[inliers], xn2[inliers])
    angle = np.degrees(np.arccos(np.clip((np.trace(R.T @ R2) - 1) / 2, -1, 1)))
    direction_cosine = abs(t @ (t2 / np.linalg.norm(t2)))
    assert angle < 1.0
    assert direction_cosine > 0.99

    good = ~np.isin(np.arange(300), bad)
    points = G.triangulate_dlt(
        K @ np.hstack([np.eye(3), np.zeros((3, 1))]),
        K @ np.hstack([R2, t2.reshape(3, 1)]),
        x1[good],
        x2[good],
    )
    mean_error = np.linalg.norm(points - X[good], axis=1).mean()
    assert mean_error < 0.05


def test_bundle_adjustment_reduces_reprojection_error(synthetic_scene):
    """Check that bundle adjustment reduces the perturbed scene's residual."""
    rng, K, X, _, t2, x1, x2, bad = synthetic_scene
    good = ~np.isin(np.arange(300), bad)
    cams = np.array(
        [
            [0, 0, 0, 0, 0, 0],
            np.r_[np.array([0.02, 0.15, -0.03]) + 0.02, t2 + 0.05],
        ]
    )
    points = X[good] + rng.normal(0, 0.05, (good.sum(), 3))
    count = good.sum()
    obs_camera = np.r_[np.zeros(count, int), np.ones(count, int)]
    obs_point = np.r_[np.arange(count), np.arange(count)]
    observations = np.vstack([x1[good], x2[good]])

    initial_error = np.abs(
        residuals(K, cams, points, obs_camera, obs_point, observations)
    ).mean()
    cameras_refined, points_refined = bundle_adjust(
        K, cams, points, obs_camera, obs_point, observations
    )
    final_error = np.abs(
        residuals(
            K,
            cameras_refined,
            points_refined,
            obs_camera,
            obs_point,
            observations,
        )
    ).mean()

    assert final_error < initial_error
    assert final_error < 1.0
