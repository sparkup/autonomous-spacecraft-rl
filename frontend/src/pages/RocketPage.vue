<template>
  <section class="page-copy">
    <h1>Launch</h1>
    <p class="text-muted mb-1">
      Launch a custom rocket state, inspect the model decision, and run a full episode.
    </p>
    <p class="text-muted">
      State fields represent: position, velocity, orientation, angular speed, and leg contacts.
      Predict runs a single decision step; Launch Rocket runs a full episode from that state.
    </p>
    <p class="text-muted mb-2">
      Select a trained run below to choose which model is used for prediction and launch.
    </p>
    <p class="text-muted technical-note mb-2">
      In practice, a selected trained run usually produces better and more stable landings than the default canonical model.
    </p>
    <div class="row g-2">
      <div class="col-md-6">
        <label class="form-label">Model run</label>
        <select v-model="selectedRun" class="form-select">
          <option value="">Default (canonical model)</option>
          <option v-for="run in availableRuns" :key="run" :value="run">{{ run }}</option>
        </select>
      </div>
    </div>

    <hr class="my-4" />
    <h2 class="h4 mb-2">Predict Action</h2>
    <p class="text-muted mb-3">Edit the 8 state values and ask the policy for the next immediate action.</p>

    <div class="row g-2">
      <div class="col-md-3" v-for="field in fields" :key="field.key">
        <label class="form-label">{{ field.label }}</label>
        <input
          v-model.number="state[field.key]"
          type="number"
          :step="field.step"
          :min="field.min"
          :max="field.max"
          class="form-control"
        />
      </div>
    </div>

    <p class="text-muted mt-3 mb-0">Example states:</p>
    <p class="mb-0"><code>-0.25,1.25,0.35,1.15,-0.50,-0.50,0,0</code></p>
    <p class="mb-0"><code>0.20,1.05,-0.10,-0.35,-0.03,0.02,0,0</code></p>
    <p class="text-muted technical-note mb-0">
      Predict returns the best immediate action for the current state only. Launch re-evaluates action at every step,
      so episode behavior can differ from the first predicted action.
    </p>
    <p class="text-muted technical-note mb-1">Input ranges and meaning:</p>
    <ul class="text-muted technical-note mb-0">
      <li><strong>Position X/Y</strong>: normalized location in the scene (<code>x: -0.75..0.75</code>, <code>y: 0.75..1.25</code>). Lower <code>y</code> is closer to terrain.</li>
      <li><strong>Velocity X/Y</strong>: normalized linear velocity (<code>-2..2</code>).</li>
      <li><strong>Angle</strong>: lander body tilt in <strong>radians</strong> (<code>-1..1</code>).</li>
      <li><strong>Angular velocity</strong>: rotational speed in normalized units (<code>-2..2</code>).</li>
      <li><strong>Left/Right leg contact</strong>: contact flags (<code>0</code> no contact, <code>1</code> contact).</li>
    </ul>
    <p class="text-muted technical-note mt-1 mb-0">
      Note: in Launch simulation, leg contacts are recomputed by physics after reset. They can affect one-step
      prediction input, but are not hard-forced during rollout because forcing contacts can create unstable states.
    </p>

    <div class="d-flex justify-content-end mt-3">
      <button class="btn btn-default" :disabled="loadingPredict" @click="predictAction">
        {{ loadingPredict ? "Predicting..." : "Predict Results" }}
      </button>
    </div>

    <pre v-if="predictResult" class="result-box mt-3">{{ JSON.stringify(predictResult, null, 2) }}</pre>
    <div v-if="predictResult" class="mt-2">
      <p class="text-muted technical-note mb-0"><strong>Action mapping:</strong> <code>0=do nothing</code>, <code>1=left engine</code>, <code>2=main engine</code>, <code>3=right engine</code>.</p>
      <p class="text-muted technical-note mb-0"><strong>Value estimate:</strong> expected return from this state (higher usually means the policy expects a better outcome).</p>
      <p class="text-muted technical-note mb-0"><strong>Probabilities:</strong> policy confidence over the 4 actions; values are between 0 and 1 and sum to 1.</p>
    </div>

    <hr class="my-4" />
    <h2 class="h4 mb-2">Launch Rocket</h2>
    <p class="text-muted mb-3">
      Run one episode using the same state above, plus rollout parameters.
    </p>

    <div class="row g-2">
      <div class="col-md-4">
        <label class="form-label">Seed</label>
        <input v-model.number="seed" type="number" class="form-control" />
      </div>
      <div class="col-md-4">
        <label class="form-label">Max steps</label>
        <input v-model.number="maxSteps" type="number" min="100" max="1000" class="form-control" />
      </div>
      <div class="col-md-4 d-flex align-items-end">
        <div>
          <div class="form-check mb-2">
          <input id="rocketDeterministic" v-model="deterministic" class="form-check-input" type="checkbox" />
          <label class="form-check-label" for="rocketDeterministic">Deterministic</label>
          </div>
        </div>
      </div>
    </div>
    <p class="text-muted technical-note mt-2 mb-0"><strong>Seed:</strong> initializes the environment randomness. Same seed + same settings usually reproduces the same episode pattern.</p>
    <p class="text-muted technical-note mb-0"><strong>Max steps:</strong> hard limit on episode length. Allowed range is <code>100..1000</code>. Launch stops when the lander terminates naturally or when this limit is reached.</p>
    <p class="text-muted technical-note mb-0"><strong>Deterministic:</strong> if enabled, the policy always picks the highest-probability action; if disabled, it can sample actions stochastically from policy probabilities.</p>

    <div class="d-flex justify-content-end mt-3">
      <button class="btn btn-primary" :disabled="loadingLaunch" @click="launchRocket">
        {{ loadingLaunch ? "Launching..." : "Launch Rocket" }}
      </button>
    </div>

    <pre v-if="rolloutSummary" class="result-box mt-3">{{ JSON.stringify(rolloutSummary, null, 2) }}</pre>

    <hr v-if="launchResult" class="my-4" />
    <div v-if="launchResult">
      <h2 class="h4 mb-3">Visual Results</h2>
      <p class="text-muted technical-note mb-0">
        <strong>Total reward</strong> is the cumulative reward collected across the episode.
        <strong>Steps</strong> is the number of simulation steps executed before stopping.
      </p>
      <p class="text-muted technical-note mb-3">
        The episode can stop because of a normal terminal condition, because <code>max_steps</code> is reached,
        or because the lander becomes unrecoverable/out of bounds (for example with high lateral velocity near the screen edge).
      </p>
      <p class="mb-1"><strong>Total reward:</strong> {{ launchResult.total_reward.toFixed(1) }}</p>
      <p class="mb-3"><strong>Steps:</strong> {{ launchResult.steps }}</p>

      <div class="row g-3">
        <div class="col-md-4" v-for="slot in frameSlots" :key="slot.key">
          <p class="mb-2"><strong>{{ slot.label }}</strong></p>
          <img
            v-if="launchResult.frames && launchResult.frames[slot.key]"
            :src="`data:image/png;base64,${launchResult.frames[slot.key]}`"
            :alt="slot.label"
            class="img-fluid rounded border"
          />
        </div>
      </div>

      <div class="d-flex justify-content-end gap-2 mt-3 flex-wrap">
        <button class="btn btn-primary" :disabled="loadingVideo" @click="generateVideo">
          {{ loadingVideo ? "Generating..." : "Generate Animation" }}
        </button>
      </div>

      <hr v-if="videoDataUrl" class="my-4" />
      <img
        v-if="videoDataUrl"
        :src="videoDataUrl"
        alt="Rocket launch animation"
        class="img-fluid w-100 rounded border mt-3"
      />
      <hr v-if="videoDataUrl" class="my-4" />
    </div>

    <p v-if="error" class="text-danger mt-3 mb-0">{{ error }}</p>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { fetchJson } from "../api";

const fields = [
  { key: "x", label: "Position X", min: -0.75, max: 0.75, step: 0.01 },
  { key: "y", label: "Position Y", min: 0.75, max: 1.25, step: 0.01 },
  { key: "vx", label: "Velocity X", min: -2, max: 2, step: 0.01 },
  { key: "vy", label: "Velocity Y", min: -2, max: 2, step: 0.01 },
  { key: "angle", label: "Angle", min: -1, max: 1, step: 0.01 },
  { key: "angular_velocity", label: "Angular velocity", min: -2, max: 2, step: 0.01 },
  { key: "left_leg", label: "Left leg contact", min: 0, max: 1, step: 1 },
  { key: "right_leg", label: "Right leg contact", min: 0, max: 1, step: 1 }
];

const frameSlots = [
  { key: "start", label: "Start" },
  { key: "middle", label: "Middle" },
  { key: "end", label: "End" }
];

const state = reactive({
  x: -0.25,
  y: 1.25,
  vx: 0.35,
  vy: 1.15,
  angle: -0.5,
  angular_velocity: -0.5,
  left_leg: 0,
  right_leg: 0
});

const seed = ref(42);
const maxSteps = ref(600);
const deterministic = ref(true);
const selectedRun = ref("");
const availableRuns = ref([]);

const loadingPredict = ref(false);
const loadingLaunch = ref(false);
const loadingVideo = ref(false);
const predictResult = ref(null);
const launchResult = ref(null);
const rolloutSummary = ref(null);
const videoDataUrl = ref("");
const error = ref("");

function observationArray() {
  return fields.map((field) => {
    let value = Number(state[field.key]);
    if (!Number.isFinite(value)) {
      value = 0;
    }
    value = Math.min(field.max, Math.max(field.min, value));
    if (field.step === 1) {
      value = Math.round(value);
    }
    state[field.key] = value;
    return value;
  });
}

function launchPayload(includeGif = false) {
  const normalizedMaxSteps = Math.min(1000, Math.max(100, Number(maxSteps.value) || 600));
  maxSteps.value = normalizedMaxSteps;
  return {
    run: selectedRun.value || null,
    observation: observationArray(),
    seed: seed.value,
    max_steps: normalizedMaxSteps,
    deterministic: deterministic.value,
    include_gif: includeGif
  };
}

async function predictAction() {
  error.value = "";
  loadingPredict.value = true;
  try {
    predictResult.value = await fetchJson("/api/predict", {
      method: "POST",
      body: JSON.stringify({
        run: selectedRun.value || null,
        observation: observationArray()
      })
    });
  } catch (err) {
    error.value = err.message;
  } finally {
    loadingPredict.value = false;
  }
}

async function launchRocket() {
  error.value = "";
  loadingLaunch.value = true;
  videoDataUrl.value = "";
  try {
    const result = await fetchJson("/interface/launch", {
      method: "POST",
      body: JSON.stringify(launchPayload(false))
    });
    launchResult.value = result;
    rolloutSummary.value = {
      total_reward: result.total_reward,
      steps: result.steps
    };
  } catch (err) {
    error.value = err.message;
  } finally {
    loadingLaunch.value = false;
  }
}

async function generateVideo() {
  error.value = "";
  loadingVideo.value = true;
  try {
    const result = await fetchJson("/interface/launch", {
      method: "POST",
      body: JSON.stringify(launchPayload(true))
    });
    launchResult.value = result;
    rolloutSummary.value = {
      total_reward: result.total_reward,
      steps: result.steps
    };
    videoDataUrl.value = result.gif_base64 ? `data:image/gif;base64,${result.gif_base64}` : "";
  } catch (err) {
    error.value = err.message;
  } finally {
    loadingVideo.value = false;
  }
}

onMounted(async () => {
  try {
    const payload = await fetchJson("/dashboard/runs");
    availableRuns.value = Array.isArray(payload?.runs) ? payload.runs : [];
  } catch (err) {
    // Keep Launch usable even if run-list fetch fails.
    availableRuns.value = [];
  }
});
</script>
