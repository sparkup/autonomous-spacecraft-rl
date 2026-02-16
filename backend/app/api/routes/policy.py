from typing import Any

import gymnasium as gym
import numpy as np
import torch
from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...core.runtime import get_model, require_run_model_or_503
from ...core.settings import MODEL_PATH

router = APIRouter(prefix="/api", tags=["api"])


class RolloutRequest(BaseModel):
    run: str | None = None
    seed: int | None = 42
    max_steps: int = Field(default=600, ge=100, le=1000)
    deterministic: bool = True


class Observation(BaseModel):
    run: str | None = None
    observation: list[float]


@router.get("")
def health() -> dict[str, Any]:
    model_loaded = True
    error: str | None = None
    try:
        get_model()
    except FileNotFoundError as exc:
        model_loaded = False
        error = str(exc)
    return {
        "status": "ok" if model_loaded else "degraded",
        "model_path": MODEL_PATH,
        "model_loaded": model_loaded,
        "error": error,
    }


@router.post("/predict")
def predict(obs: Observation) -> dict[str, Any]:
    model = require_run_model_or_503(obs.run)
    # SB3 predict expects batch-shaped input: (batch_size, obs_dim).
    state = np.array(obs.observation).reshape(1, -1)
    action, _ = model.predict(state, deterministic=True)
    # Discrete action can come as ndarray; normalize to plain int for API JSON.
    action_value = int(np.asarray(action).reshape(-1)[0])
    tensor_state = torch.as_tensor(state).float()
    value = model.policy.predict_values(tensor_state).item()
    # Distribution probs shape is (batch_size, n_actions); keep it as list for frontend introspection.
    probs = (
        model.policy.get_distribution(tensor_state)
        .distribution.probs.detach()
        .numpy()
        .tolist()
    )

    return {
        "action": action_value,
        "value_estimate": value,
        "probabilities": probs,
    }


@router.post("/rollout")
def rollout(req: RolloutRequest) -> dict[str, Any]:
    model = require_run_model_or_503(req.run)
    env = gym.make("LunarLander-v3")
    obs, _ = env.reset(seed=req.seed)
    total_reward = 0.0
    steps = 0

    while steps < req.max_steps:
        action, _ = model.predict(obs, deterministic=req.deterministic)
        obs, reward, terminated, truncated, _ = env.step(action)
        total_reward += float(reward)
        steps += 1
        # Stop as soon as env ends naturally; max_steps is only a safety cap.
        if terminated or truncated:
            break

    env.close()
    return {"total_reward": total_reward, "steps": steps}
