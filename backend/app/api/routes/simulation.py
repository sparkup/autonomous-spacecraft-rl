import base64
import io
from typing import Any

import gymnasium as gym
import numpy as np
from fastapi import APIRouter, HTTPException
from gymnasium.envs.box2d import lunar_lander as ll
from PIL import Image
from pydantic import BaseModel, Field, field_validator

from ...core.runtime import require_run_model_or_503

router = APIRouter(prefix="/interface", tags=["interface"])


class InterfaceRunRequest(BaseModel):
    run: str | None = None
    seed: int = 42
    deterministic: bool = True
    max_steps: int = Field(default=600, ge=100, le=1000)


class TestRocketRequest(BaseModel):
    run: str | None = None
    observation: list[float] = Field(
        ...,
        description="LunarLander observation vector [x, y, vx, vy, angle, angular_velocity, left_leg, right_leg]",
    )
    seed: int = 42
    deterministic: bool = True
    max_steps: int = Field(default=600, ge=100, le=1000)
    include_gif: bool = False

    @field_validator("observation")
    @classmethod
    def validate_observation(cls, value: list[float]) -> list[float]:
        if len(value) != 8:
            raise ValueError("observation must contain exactly 8 values")
        return value


def _frame_to_base64_png(frame: Any) -> str:
    image = Image.fromarray(frame)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _frames_to_base64_gif(frames: list[Any], max_frames: int = 120) -> str | None:
    if not frames:
        return None
    # Down-sample long trajectories to bound GIF size and response payload time.
    stride = max(1, len(frames) // max_frames)
    sampled = frames[::stride]
    images = [Image.fromarray(frame) for frame in sampled]
    buf = io.BytesIO()
    images[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=60,
        loop=0,
        optimize=False,
    )
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _apply_observation_override(env: gym.Env, observation: list[float]) -> np.ndarray:
    """Map normalized LunarLander observation values back to physical lander state."""
    uw = env.unwrapped
    if not hasattr(uw, "lander") or uw.lander is None:
        raise HTTPException(status_code=500, detail="Lander body not initialized")

    x, y, vx, vy, angle, ang_vel, leg_l, leg_r = [float(v) for v in observation]

    # Keep custom starts inside a physically stable range to avoid broken joints/explosions.
    x = float(np.clip(x, -0.95, 0.95))
    y = float(np.clip(y, -0.95, 1.25))
    vx = float(np.clip(vx, -2.0, 2.0))
    vy = float(np.clip(vy, -2.0, 2.0))
    angle = float(np.clip(angle, -1.0, 1.0))
    ang_vel = float(np.clip(ang_vel, -2.0, 2.0))

    # Convert normalized observation space back into Box2D world coordinates.
    half_w = ll.VIEWPORT_W / ll.SCALE / 2
    half_h = ll.VIEWPORT_H / ll.SCALE / 2

    pos_x = x * half_w + half_w
    pos_y = y * half_h + (uw.helipad_y + ll.LEG_DOWN / ll.SCALE)
    vel_x = vx * ll.FPS / half_w
    vel_y = vy * ll.FPS / half_h
    angular_velocity = ang_vel * ll.FPS / 20.0

    uw.lander.position = (pos_x, pos_y)
    uw.lander.linearVelocity = (vel_x, vel_y)
    uw.lander.angle = angle
    uw.lander.angularVelocity = angular_velocity

    # Move legs consistently with the lander transform so joints remain stable.
    if hasattr(uw, "legs") and len(uw.legs) >= 2:
        for i, leg in zip([-1, +1], uw.legs):
            leg.position = (pos_x - i * ll.LEG_AWAY / ll.SCALE, pos_y)
            leg.linearVelocity = (vel_x, vel_y)
            leg.angle = angle + (i * 0.05)
            leg.angularVelocity = angular_velocity
            leg.awake = True

    uw.lander.awake = True

    if hasattr(uw, "legs") and len(uw.legs) >= 2:
        # Contact flags are environment outputs; forcing them can produce invalid states.
        uw.legs[0].ground_contact = False
        uw.legs[1].ground_contact = False

    return np.array([x, y, vx, vy, angle, ang_vel, leg_l, leg_r], dtype=np.float32)


@router.get("")
def interface_info() -> dict[str, str]:
    return {
        "title": "Eagle-1 Interface",
        "description": "Run one episode and inspect start/middle/end frames.",
    }


@router.post("/run")
def run_episode(req: InterfaceRunRequest) -> dict[str, Any]:
    model = require_run_model_or_503(req.run)
    env = gym.make("LunarLander-v3", render_mode="rgb_array")
    obs, _ = env.reset(seed=int(req.seed))
    frames = []
    total_reward = 0.0
    steps = 0

    while True:
        action, _ = model.predict(obs, deterministic=req.deterministic)
        obs, reward, terminated, truncated, _ = env.step(action)
        frame = env.render()
        if frame is not None:
            frames.append(frame)
        total_reward += float(reward)
        steps += 1
        # Either episode finished by environment or we hit explicit user step limit.
        if terminated or truncated or steps >= req.max_steps:
            break

    env.close()

    if not frames:
        return {
            "total_reward": total_reward,
            "steps": steps,
            "frames": {"start": None, "middle": None, "end": None},
        }

    middle_idx = len(frames) // 2
    payload = {
        "start": _frame_to_base64_png(frames[0]),
        "middle": _frame_to_base64_png(frames[middle_idx]),
        "end": _frame_to_base64_png(frames[-1]),
    }

    return {
        "total_reward": total_reward,
        "steps": steps,
        "frames": payload,
    }


@router.post("/launch")
@router.post("/test-rocket")
def launch(req: TestRocketRequest) -> dict[str, Any]:
    model = require_run_model_or_503(req.run)
    env = gym.make("LunarLander-v3", render_mode="rgb_array")
    _, _ = env.reset(seed=int(req.seed))

    # Start from user-defined state rather than default env reset state.
    obs = _apply_observation_override(env, req.observation)
    action, _ = model.predict(obs, deterministic=req.deterministic)
    predicted_action = int(np.asarray(action).reshape(-1)[0])

    frames = []
    initial_frame = env.render()
    if initial_frame is not None:
        frames.append(initial_frame)

    total_reward = 0.0
    steps = 0
    while steps < req.max_steps:
        action, _ = model.predict(obs, deterministic=req.deterministic)
        obs, reward, terminated, truncated, _ = env.step(action)
        frame = env.render()
        if frame is not None:
            frames.append(frame)
        total_reward += float(reward)
        steps += 1
        if terminated or truncated:
            break

    env.close()

    if not frames:
        return {
            "predicted_action": predicted_action,
            "total_reward": total_reward,
            "steps": steps,
            "frames": {"start": None, "middle": None, "end": None},
            "gif_base64": None,
        }

    mid = len(frames) // 2
    return {
        "predicted_action": predicted_action,
        "total_reward": total_reward,
        "steps": steps,
        "frames": {
            "start": _frame_to_base64_png(frames[0]),
            "middle": _frame_to_base64_png(frames[mid]),
            "end": _frame_to_base64_png(frames[-1]),
        },
        "gif_base64": _frames_to_base64_gif(frames) if req.include_gif else None,
    }
