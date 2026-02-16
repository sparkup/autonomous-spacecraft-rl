"""Runtime utilities for model loading and run-path resolution."""

from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException
from stable_baselines3 import PPO

from .settings import MODEL_PATH, RUNS_BASE_DIR


def project_root() -> Path:
    """Resolve backend paths from current working directory."""
    return Path.cwd()


def resolve_path(path_str: str) -> Path:
    """Resolve absolute/relative filesystem path for runtime assets."""
    path = Path(path_str)
    if path.is_absolute():
        return path
    return project_root() / path


@lru_cache(maxsize=1)
def get_model() -> PPO:
    """Load and cache the PPO policy used by API endpoints."""
    return _load_model(str(resolve_path(MODEL_PATH)))


@lru_cache(maxsize=32)
def _load_model(model_path: str) -> PPO:
    """Load and cache a PPO model from a concrete filesystem path."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Model file not found at {path}. Please train or copy it before running the API."
        )
    return PPO.load(str(path))


def _resolve_run_model_path(run: str | None) -> Path:
    """Resolve the model path for a selected run or canonical default model."""
    if not run:
        return resolve_path(MODEL_PATH)

    run_dir = resolve_runs_base_dir() / run
    # Prefer explicit run artifact first, then fallback to eval-selected best checkpoint.
    candidates = [
        run_dir / "ppo_lander_baseline.zip",
        run_dir / "best_model.zip",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def require_run_model_or_503(run: str | None) -> PPO:
    """Load selected run model (or default model) and expose user-friendly 503 on failure."""
    try:
        path = _resolve_run_model_path(run)
        # Cached by model path, so switching run keeps each model loaded once per process.
        return _load_model(str(path))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def resolve_runs_base_dir() -> Path:
    """Resolve run directory with fallback for local notebook execution."""
    base = resolve_path(RUNS_BASE_DIR)
    if base.exists():
        return base
    fallback = project_root() / "runs" / "lander_baseline"
    return fallback


def list_runs() -> list[str]:
    """List available run folder names sorted alphabetically."""
    base_dir = resolve_runs_base_dir()
    if not base_dir.exists():
        return []
    return sorted([p.name for p in base_dir.iterdir() if p.is_dir()])
