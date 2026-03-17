# Autonomous Spacecraft

> A **reinforcement learning (RL) demonstration** for descent control, built around `LunarLander-v3` with a scientific, incremental methodology from first principles to mission-level integration.

## Project Overview

**Autonomous Spacecraft** is not presented as a single benchmark score challenge.  
It is structured as an **engineering-scientific progression**:

- Start with simple and controlled assumptions
- Validate each technical layer independently
- Increase algorithmic complexity across launches
- Then consolidate into a deployable end-to-end demo (frontend + backend + notebooks + training pipeline)

The core objective is to demonstrate sound RL reasoning, reproducibility, and clear technical communication for a guidance-and-landing style task.

## Live Demo

- [Main demo](https://autonomous-spacecraft.demo.sparkup.dev)
- [Launch page](https://autonomous-spacecraft.demo.sparkup.dev/launch)
- [Dashboard page](https://autonomous-spacecraft.demo.sparkup.dev/dashboard)

## Product Pages

The current web application is intentionally focused on three pages:

- **Home**
    - Project intent and scientific context
    - High-level explanation of endpoints and state format
    - Run-awareness and reproducibility framing

- **Launch**
    - One-step policy inference from a custom state
    - Full episode rollout from that state
    - Visual outputs (start/middle/end frames + animation)
    - Run selection to compare model behavior

- **Dashboard**
    - Training/evaluation analysis by run
    - Timestep filtering and downsampling controls
    - Smoothing and chart mode selection
    - Mean reward, variability, and success-rate trend inspection

## Scientific Notebook Track

The `notebook/` sequence is the methodological backbone of the project:

- **Launch 1** (`notebook/launch-1.ipynb`)  
  RL foundations, environment instrumentation, baseline behavior and protocol validation.

- **Launch 2** (`notebook/launch-2.ipynb`)  
  Tabular Q-learning phase to establish interpretable learning dynamics before deep policies.

- **Launch 3** (`notebook/launch-3.ipynb`)  
  Deep RL transition (DQN stage), functional approximation, replay/target stabilization concepts, quantitative and qualitative evaluation.

- **Mission** (`notebook/mission.ipynb`)  
  PPO mission baseline with training/evaluation workflow, model export, telemetry integration, and deployment-ready usage.

Across these notebooks, the project now explicitly documents:

- Why PPO is selected for the mission phase
- Why LunarLander is used as a controlled proxy
- Reward interpretation and shaping implications
- Variance handling (seeds, repeated evals, smoothing)
- Simulation limits and Sim2Real gap

## Why PPO for Mission Baseline

For the integrated mission phase, PPO is chosen as a practical stability/performance trade-off:

- Clipped objective to reduce destructive policy jumps
- Robust and reproducible training behavior in standard toolchains
- Strong fit for iterative policy improvement in benchmark control tasks

This repository demonstrates a **credible baseline approach**, not a claim of direct real-flight transfer.

## Architecture Overview

The repository is organized as a modular full-stack RL demo:

- `frontend/` : Vue + Vite user interface
- `backend/` : FastAPI API and inference runtime
    - `backend/app/api/routes/policy.py` : predict/rollout endpoints
    - `backend/app/api/routes/simulation.py` : launch/interface visual simulation endpoints
    - `backend/app/api/routes/telemetry.py` : dashboard run/metrics endpoints
    - `backend/app/core/runtime.py` : model loading and run resolution
    - `backend/app/core/settings.py` : environment-based settings
- `backend/model/generate.py` : PPO training/generation entrypoint
- `notebook/` : launch-to-mission scientific progression
- `docker-compose.yml` : local stack (frontend, backend, notebook)
- `stack.yml` : production stack deployment definition

## Repository Structure

```text
backend/
  app/
    api/routes/
    core/
  model/
  runs/
frontend/
notebook/
docker-compose.yml
README.md
```

## Data Persistence (Runs)

Training/evaluation runs are persisted through a named Docker volume mounted at:

- `/app/backend/runs`

Volume name:

- `autonomous-spacecraft-runs`

This is configured in both `docker-compose.yml` and `stack.yml` to avoid losing runs when containers are recreated.

## Environment Configuration

Environment templates are split by service:

- `backend/.env.example`
- `frontend/.env.example`

Typical backend variables:

- `MODEL_PATH`
- `RUNS_BASE_DIR`
- `CORS_ORIGINS`

Typical frontend variables:

- `VITE_BACKEND_BASE_URL`
- `VITE_SPARKUP_STATIC_BASE`
- `VITE_SPARKUP_PORTFOLIO_URL`
- `VITE_REPO_URL`

## Local Development

From project root:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up -d --build
```

Default local endpoints:

- Frontend: `https://autonomous-spacecraft.demo.sparkup.local`
- Backend docs: `https://api-autonomous-spacecraft.demo.sparkup.local/docs`
- Notebooks: `http://localhost:8888`

## Model Generation

Train/generate PPO model locally:

```bash
python -m backend.model.generate --timesteps 300000
```

Or from Docker backend container:

```bash
docker compose exec backend python -m backend.model.generate --timesteps 300000
```

Generated artifacts are saved under `backend/runs/lander_baseline/` and become selectable in Launch and Dashboard.

## Scientific Scope and Limits

This project intentionally remains a controlled simulation demo.  
It does not model full aerospace operational constraints (high-fidelity aerodynamics, full sensor/actuator uncertainty, fault handling, certification constraints).

The value is in the **methodology**: transparent assumptions, measurable progression, reproducible experimentation, and clear communication of limits and next steps.
