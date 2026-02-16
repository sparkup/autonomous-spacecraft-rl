<template>
  <section class="page-copy">
    <div class="d-flex flex-column flex-lg-row gap-4 align-items-start">
      <img :src="heroImage" alt="Lunar lander mission" class="home-hero-image" />
      <div>
        <h1>Autonomous Spacecraft</h1>
        <p class="text-muted">
          This demo showcases a PPO policy trained on <strong>LunarLander-v3</strong>. PPO is a
          <strong>reinforcement learning</strong> method, and reinforcement learning is a subcategory of AI where
          an agent learns by trial and error with rewards.
        </p>
        <p class="text-muted">
          You can test custom spacecraft states, launch full episodes, and inspect training behavior across runs.
          The full source code, training scripts, and notebooks are available on
          <a :href="repoUrl" target="_blank" rel="noopener">GitHub</a>.
        </p>
      </div>
    </div>
    <p class="text-muted technical-note mt-3 mb-0">
      <em><strong>Technical note:</strong> frontend is Vue + Vite and backend is FastAPI. The policy model is
      PPO (Stable-Baselines3) trained on LunarLander-v3 (Gymnasium Box2D), using the 8-value state vector
      <code>[x, y, vx, vy, angle, angular_velocity, left_leg_contact, right_leg_contact]</code>. Launch endpoints run deterministic or
      stochastic rollouts and Dashboard reads saved evaluation runs to visualize reward and success trends.</em>
    </p>

    <hr class="my-4" />
    <h2 class="h4 mb-3">Mission Modules</h2>
    <ul class="mb-0">
      <li><strong>Launch:</strong> enter the 8-value state vector, get a one-step prediction, run an episode, and generate a GIF.</li>
      <li><strong>Dashboard:</strong> compare evaluation runs with smoothing and point limits to understand training quality.</li>
    </ul>

    <hr class="my-4" />
    <h2 class="h5 mb-2">Scientific Approach</h2>
    <p class="text-muted mb-2">
      The project follows an incremental notebook track, from RL fundamentals to a mission-ready PPO baseline.
      This progression documents assumptions, experiments, variance handling, and interpretation of results.
    </p>
    <ul class="mb-0">
      <li><strong>Launch 1:</strong> <a :href="`${notebookBaseUrl}/launch-1.ipynb`" target="_blank" rel="noopener">notebook/launch-1.ipynb</a></li>
      <li><strong>Launch 2:</strong> <a :href="`${notebookBaseUrl}/launch-2.ipynb`" target="_blank" rel="noopener">notebook/launch-2.ipynb</a></li>
      <li><strong>Launch 3:</strong> <a :href="`${notebookBaseUrl}/launch-3.ipynb`" target="_blank" rel="noopener">notebook/launch-3.ipynb</a></li>
      <li><strong>Mission:</strong> <a :href="`${notebookBaseUrl}/mission.ipynb`" target="_blank" rel="noopener">notebook/mission.ipynb</a></li>
    </ul>

    <hr class="my-4" />
    <h2 class="h5 mb-2">How It Works</h2>
    <p class="mb-2">
      <strong><code>/api/predict</code></strong> returns the immediate action, value estimate, and action probabilities
      for one observation vector.
    </p>
    <p class="mb-2">
      <strong><code>/api/rollout</code></strong> runs a full seeded episode and returns <code>total_reward</code> and <code>steps</code>.
    </p>
    <p class="mb-2">
      <strong><code>/interface/launch</code></strong> starts from your custom state, runs the policy, and returns summary + start/middle/end frames (+ optional GIF).
    </p>
    <p class="mb-0">
      <strong><code>/dashboard/data</code></strong> provides run metrics used for reward/success trend visualization.
    </p>

    <hr class="my-4" />
    <h2 class="h5 mb-2">State Vector Format</h2>
    <p class="mb-0"><code>[x, y, vx, vy, angle, angular_velocity, left_leg_contact, right_leg_contact]</code></p>

    <hr class="my-4" />
    <h2 class="h5 mb-2">Available Trained Runs</h2>
    <p v-if="runsError" class="text-danger mb-0">{{ runsError }}</p>
    <div v-else-if="runs.length > 0">
      <p class="text-muted mb-2">Detected run folders on this instance:</p>
      <ul class="mb-2">
        <li v-for="run in runs" :key="run"><code>{{ run }}</code></li>
      </ul>
      <p class="mb-0 text-muted">
        You can train your own models and add new runs; check the repository docs and notebooks for training commands.
      </p>
    </div>
    <p v-else class="mb-0 text-muted">No run folders detected yet on this instance.</p>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { fetchJson } from "../api";
import launchImage from "../assets/images/launch.png";

const heroImage = launchImage;
const repoUrl = import.meta.env.VITE_REPO_URL || "https://github.com/sparkup/autonomous-spacecraft-rl";
const notebookBaseUrl = `${repoUrl.replace(/\/$/, "")}/blob/main/notebook`;

const runs = ref([]);
const runsError = ref("");

onMounted(async () => {
  try {
    const payload = await fetchJson("/dashboard/runs");
    runs.value = Array.isArray(payload?.runs) ? payload.runs : [];
  } catch (err) {
    runsError.value = err.message;
  }
});
</script>
