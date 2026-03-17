from pathlib import Path
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException, Query

from ...core.runtime import resolve_runs_base_dir

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])
rocket_router = APIRouter(prefix="/rocket", tags=["rocket"])


def _list_runs(base_dir: Path) -> list[str]:
    if not base_dir.exists():
        return []
    return sorted([p.name for p in base_dir.iterdir() if p.is_dir()])


def _run_npz_path(base_dir: Path, run: str | None) -> Path:
    runs = _list_runs(base_dir)
    if not runs:
        raise HTTPException(status_code=404, detail=f"No run directories found in {base_dir}")

    # Graceful fallback: if run is missing/invalid, use the first available run.
    selected = run if run in runs else runs[0]
    npz_path = base_dir / selected / "evaluations.npz"
    if not npz_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No evaluations.npz found in run '{selected}'",
        )
    return npz_path


def _find_latest_evaluations_npz(base_dir: Path) -> Path | None:
    direct = base_dir / "evaluations.npz"
    if direct.exists():
        return direct

    if not base_dir.exists():
        return None

    candidates = sorted(
        [p for p in base_dir.glob("*/evaluations.npz") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _public_runs_path(path: Path) -> str:
    """
    Convert internal filesystem paths to a safe, frontend-facing path.

    Example:
    /app/backend/runs/lander_baseline/run-.../evaluations.npz
      -> ./runs/lander_baseline/run-.../evaluations.npz
    """
    raw = path.as_posix()
    for marker in ("/backend/runs/", "/runs/"):
        if marker in raw:
            suffix = raw.split(marker, 1)[1].lstrip("/")
            return f"./runs/{suffix}"
    return f"./{path.name}"


@dashboard_router.get("")
def dashboard_info() -> dict[str, str]:
    return {
        "title": "Eagle-1 Dashboard",
        "description": "Evaluation metrics with filtering and smoothing.",
    }


@dashboard_router.get("/runs")
def runs() -> dict[str, Any]:
    base_dir = resolve_runs_base_dir()
    return {
        "base_dir": _public_runs_path(base_dir),
        "runs": _list_runs(base_dir),
    }


@dashboard_router.get("/data")
def dashboard_data(
    run: str | None = None,
    min_timestep: int | None = None,
    max_timestep: int | None = None,
    max_points: int | None = Query(default=None, ge=3, le=30),
    smoothing_window: int = Query(default=5, ge=1, le=15),
    success_threshold: float = 200.0,
) -> dict[str, Any]:
    base_dir = resolve_runs_base_dir()
    npz_path = _run_npz_path(base_dir, run)

    # SB3 EvalCallback writes timesteps/results arrays in evaluations.npz.
    data = np.load(npz_path, allow_pickle=True)
    all_timesteps = data["timesteps"]
    timesteps = all_timesteps
    results = data["results"]

    if len(all_timesteps) == 0:
        raise HTTPException(status_code=404, detail="No evaluation timesteps found")

    run_min_timestep = int(np.min(all_timesteps))
    run_max_timestep = int(np.max(all_timesteps))

    mean_rewards = results.mean(axis=1)
    std_rewards = results.std(axis=1)
    success_rate = np.mean(results > success_threshold, axis=1) * 100

    if min_timestep is not None:
        mask_min = timesteps >= min_timestep
        timesteps = timesteps[mask_min]
        mean_rewards = mean_rewards[mask_min]
        std_rewards = std_rewards[mask_min]
        success_rate = success_rate[mask_min]

    if max_timestep is not None:
        mask_max = timesteps <= max_timestep
        timesteps = timesteps[mask_max]
        mean_rewards = mean_rewards[mask_max]
        std_rewards = std_rewards[mask_max]
        success_rate = success_rate[mask_max]

    if max_points is not None and len(timesteps) > max_points:
        # Keep points bounded while preserving full training span (start -> end).
        indices = np.linspace(0, len(timesteps) - 1, num=max_points, dtype=int)
        timesteps = timesteps[indices]
        mean_rewards = mean_rewards[indices]
        std_rewards = std_rewards[indices]
        success_rate = success_rate[indices]

    if len(timesteps) == 0:
        raise HTTPException(status_code=404, detail="No data points after filtering")

    if len(mean_rewards) >= smoothing_window:
        # Moving-average smoothing is applied on the filtered window only.
        kernel = np.ones(smoothing_window) / smoothing_window
        smoothed_mean = np.convolve(mean_rewards, kernel, mode="valid")
        smoothed_success = np.convolve(success_rate, kernel, mode="valid")
        smoothed_timesteps = timesteps[smoothing_window - 1 :]
    else:
        smoothed_mean = mean_rewards
        smoothed_success = success_rate
        smoothed_timesteps = timesteps

    return {
        "npz_path": _public_runs_path(npz_path),
        "run_min_timestep": run_min_timestep,
        "run_max_timestep": run_max_timestep,
        "timesteps": timesteps.tolist(),
        "mean_rewards": mean_rewards.tolist(),
        "std_rewards": std_rewards.tolist(),
        "success_rate": success_rate.tolist(),
        "smoothed_timesteps": smoothed_timesteps.tolist(),
        "smoothed_mean": smoothed_mean.tolist(),
        "smoothed_success_rate": smoothed_success.tolist(),
        "smoothing_window": smoothing_window,
        "points": int(len(timesteps)),
    }


@rocket_router.get("")
def rocket_data() -> dict[str, Any]:
    base_dir = resolve_runs_base_dir()
    npz_path = _find_latest_evaluations_npz(base_dir)
    if npz_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"No evaluations.npz found in {base_dir}",
        )

    data = np.load(npz_path, allow_pickle=True)
    timesteps = data["timesteps"]
    results = data["results"]
    mean_rewards = results.mean(axis=1)
    std_rewards = results.std(axis=1)

    return {
        "npz_path": _public_runs_path(npz_path),
        "timesteps": timesteps.tolist(),
        "mean_rewards": mean_rewards.tolist(),
        "std_rewards": std_rewards.tolist(),
        "count": int(len(mean_rewards)),
    }
