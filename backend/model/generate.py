"""CLI helper to train and export the LunarLander baseline model.

Usage:
  python -m backend.model.generate --timesteps 300000
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.monitor import Monitor


def parse_args() -> argparse.Namespace:
    """Parse CLI args for a reproducible PPO training run."""
    parser = argparse.ArgumentParser(description="Train PPO baseline for LunarLander-v3")
    parser.add_argument("--timesteps", type=int, default=300_000, help="Total training timesteps")
    parser.add_argument("--eval-freq", type=int, default=10_000, help="Evaluation frequency in timesteps")
    parser.add_argument("--n-eval-episodes", type=int, default=10, help="Episodes per periodic evaluation")
    parser.add_argument("--run-name", type=str, default="", help="Optional run folder name")
    parser.add_argument("--env-id", type=str, default="LunarLander-v3", help="Gymnasium environment id")
    return parser.parse_args()


def ensure_paths(run_name: str) -> tuple[Path, Path]:
    """Create and return baseline run directories.

    Returns:
      - base_dir: shared location for all LunarLander runs.
      - run_dir:  specific run directory (timestamped if no run-name is provided).
    """
    base_dir = Path("backend/runs/lander_baseline")
    base_dir.mkdir(parents=True, exist_ok=True)

    if run_name:
        run_dir = base_dir / run_name
    else:
        stamp = dt.datetime.now().strftime("run-%Y%m%d-%H%M%S")
        run_dir = base_dir / stamp

    run_dir.mkdir(parents=True, exist_ok=True)
    return base_dir, run_dir


def train(args: argparse.Namespace) -> int:
    """Train PPO model, save run artifacts, and print summary metrics."""
    base_dir, run_dir = ensure_paths(args.run_name)

    # Train/eval envs are intentionally separated:
    # - train_env collects learning experience and monitor logs
    # - eval_env is used by EvalCallback/evaluate_policy for unbiased checks
    train_env = Monitor(
        gym.make(args.env_id),
        filename=str(run_dir / "monitor.csv"),
    )
    eval_env = Monitor(gym.make(args.env_id))

    # EvalCallback periodically scores the policy and stores the best checkpoint.
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(run_dir),
        log_path=str(run_dir),
        eval_freq=args.eval_freq,
        n_eval_episodes=args.n_eval_episodes,
        deterministic=True,
        render=False,
    )

    # Baseline PPO configuration tuned for stable first-pass training.
    model = PPO(
        "MlpPolicy",
        train_env,
        verbose=1,
        tensorboard_log=str(run_dir),
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.0,
        clip_range=0.2,
    )

    # Core optimization loop.
    model.learn(total_timesteps=args.timesteps, callback=eval_callback)

    # Run-specific checkpoint: keeps historical artifacts for comparison.
    run_model_prefix = run_dir / "ppo_lander_baseline"
    model.save(str(run_model_prefix))

    # Canonical model location used by backend API/frontend runtime loading.
    # This path is intentionally overwritten by latest training run.
    canonical_model_prefix = base_dir / "ppo_lander_baseline"
    model.save(str(canonical_model_prefix))

    # Final post-training evaluation for quick CLI feedback.
    mean_reward, std_reward = evaluate_policy(
        model,
        eval_env,
        n_eval_episodes=max(5, args.n_eval_episodes),
        deterministic=True,
    )

    train_env.close()
    eval_env.close()

    print("Training complete.")
    print(f"Run directory: {run_dir}")
    print(f"Run model: {run_model_prefix}.zip")
    print(f"Canonical model: {canonical_model_prefix}.zip")
    print(f"Evaluation mean reward: {mean_reward:.2f} ± {std_reward:.2f}")
    return 0


def main() -> int:
    """Entrypoint for `python -m backend.model.generate`."""
    args = parse_args()
    return train(args)


if __name__ == "__main__":
    raise SystemExit(main())
