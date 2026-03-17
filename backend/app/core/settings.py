"""Application-level constants and environment-driven configuration."""

from os import getenv

APP_TITLE = "Autonomous Spacecraft Backend"
APP_VERSION = "0.3.0"

DEFAULT_MODEL_PATH = "backend/runs/lander_baseline/ppo_lander_baseline.zip"
DEFAULT_RUNS_BASE_DIR = "backend/runs/lander_baseline"

MODEL_PATH = getenv("MODEL_PATH", DEFAULT_MODEL_PATH)
RUNS_BASE_DIR = getenv("RUNS_BASE_DIR", DEFAULT_RUNS_BASE_DIR)

# Comma-separated list in CORS_ORIGINS env var.
CORS_ORIGINS = [
    origin.strip()
    for origin in getenv("CORS_ORIGINS").split(",")
    if origin.strip()
]
