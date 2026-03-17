<template>
  <section class="page-copy">
    <h1>Dashboard</h1>
    <p class="text-muted mb-1">
      Explore how the trained agent progresses over evaluation checkpoints.
    </p>
    <p class="text-muted">
      Use this page to compare run behavior through multiple chart types: raw mean reward, reward standard deviation,
      smoothed mean reward, and success rate. Data refreshes automatically when values change.
    </p>

    <hr class="my-4" />
    <div class="row g-2">
      <div class="col-md-4">
        <label class="form-label">Run</label>
        <select v-model="selectedRun" class="form-select">
          <option v-for="run in runs" :key="run" :value="run">{{ run }}</option>
        </select>
      </div>
      <div class="col-md-4">
        <label class="form-label">Min timestep</label>
        <input
          v-model.number="minTimestep"
          type="number"
          :min="Number.isFinite(availableMinTimestep) ? availableMinTimestep : 0"
          :max="Number.isFinite(availableMaxTimestep) ? availableMaxTimestep : undefined"
          @blur="normalizeField('min')"
          class="form-control"
        />
      </div>
      <div class="col-md-4">
        <label class="form-label">Max timestep</label>
        <input
          v-model.number="maxTimestep"
          type="number"
          :min="Number.isFinite(availableMinTimestep) ? availableMinTimestep : 0"
          :max="Number.isFinite(availableMaxTimestep) ? availableMaxTimestep : undefined"
          @blur="normalizeField('max')"
          class="form-control"
        />
      </div>
      <div class="col-md-6 mt-3">
        <label class="form-label">Max points (3..30)</label>
        <input v-model.number="maxPoints" type="range" min="3" max="30" class="form-range" />
        <div class="small text-muted">Current: {{ maxPoints }}</div>
      </div>
      <div class="col-md-6 mt-3">
        <label class="form-label">Smoothing window (1..15)</label>
        <input v-model.number="smoothingWindow" type="range" min="1" max="15" class="form-range" />
        <div class="small text-muted">Current: {{ smoothingWindow }}</div>
      </div>
      <div class="col-md-6 mt-3 d-flex align-items-end">
        <div class="form-check mb-2">
          <input id="showStdBand" v-model="showStdBand" class="form-check-input" type="checkbox" />
          <label class="form-check-label" for="showStdBand">
            Show ±1σ band on mean reward chart
          </label>
        </div>
      </div>
      <div class="col-md-6 mt-3">
        <label class="form-label">Chart to display</label>
        <select v-model="chartType" class="form-select">
          <option value="mean">Mean reward</option>
          <option value="std">Reward standard deviation</option>
          <option value="smoothed_mean">Smoothed mean reward</option>
          <option value="success">Success rate (%)</option>
        </select>
      </div>
    </div>

    <div class="mt-3 technical-note text-muted">
      <p class="mb-2">
        <em><strong>Technical notes:</strong> <code>Min timestep</code> and <code>Max timestep</code> restrict the
        section of training history used to build the chart. Leave <code>Max timestep</code> empty to include all
        remaining data after the minimum.</em>
      </p>
      <p class="mb-2">
        <em><code>Max points</code> controls the number of sampled evaluation points rendered on the chart and is
        constrained to <strong>3..30</strong>. <code>Smoothing window</code> controls the moving average window (in
        evaluation points) and is constrained to <strong>1..15</strong>.</em>
      </p>
      <p class="mb-0">
        <em><code>Chart to display</code> switches the metric: mean reward (raw performance), reward standard
        deviation (stability/variance), smoothed mean reward (trend readability), and success rate (percentage of
        evaluations above success threshold). <code>Show ±1σ band</code> overlays uncertainty around mean reward.</em>
      </p>
    </div>

    <p v-if="error" class="text-danger mt-3 mb-0">{{ error }}</p>

    <hr v-if="data" class="my-4" />
    <div v-if="data">
      <p class="mb-1"><strong>Source:</strong> <code>{{ safeNpzPath }}</code></p>
      <p class="mb-3"><strong>Points:</strong> {{ data.points }}</p>

      <svg
        v-if="linePoints.length > 1"
        class="chart"
        :viewBox="`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`"
        preserveAspectRatio="none"
      >
        <g>
          <line
            v-for="tick in yAxisTicks"
            :key="`y-grid-${tick.y}`"
            :x1="CHART_LEFT"
            :y1="tick.y"
            :x2="CHART_RIGHT"
            :y2="tick.y"
            stroke="rgba(15, 23, 42, 0.10)"
            stroke-width="1"
          />
          <text
            v-for="tick in yAxisTicks"
            :key="`y-label-${tick.y}`"
            :x="CHART_LEFT - 8"
            :y="tick.y + 4"
            text-anchor="end"
            fill="rgba(15, 23, 42, 0.7)"
            font-size="10"
          >
            {{ tick.label }}
          </text>

          <line
            v-for="tick in xAxisTicks"
            :key="`x-grid-${tick.x}`"
            :x1="tick.x"
            :y1="CHART_TOP"
            :x2="tick.x"
            :y2="CHART_BOTTOM"
            stroke="rgba(15, 23, 42, 0.06)"
            stroke-width="1"
          />
          <text
            v-for="tick in xAxisTicks"
            :key="`x-label-${tick.x}`"
            :x="tick.x"
            :y="CHART_BOTTOM + 15"
            :text-anchor="tick.anchor"
            fill="rgba(15, 23, 42, 0.7)"
            font-size="10"
          >
            {{ tick.label }}
          </text>
        </g>

        <line :x1="CHART_LEFT" :y1="CHART_BOTTOM" :x2="CHART_RIGHT" :y2="CHART_BOTTOM" stroke="rgba(15, 23, 42, 0.35)" />
        <line :x1="CHART_LEFT" :y1="CHART_TOP" :x2="CHART_LEFT" :y2="CHART_BOTTOM" stroke="rgba(15, 23, 42, 0.35)" />

        <polygon
          v-if="stdBandPoints && chartType === 'mean' && showStdBand"
          :points="stdBandPoints"
          fill="rgba(91, 70, 214, 0.20)"
          stroke="none"
        />
        <polyline :points="linePoints" fill="none" :stroke="lineColor" stroke-width="3" />
        <polyline
          v-if="overlayPoints"
          :points="overlayPoints"
          fill="none"
          stroke="#7d3c98"
          stroke-width="2"
          stroke-dasharray="4 3"
        />
      </svg>

      <div class="row g-3 mt-1">
        <div class="col-md-6">
          <h3 class="h6">{{ primaryLabel }}</h3>
          <p class="mb-0">Last: {{ primaryLast.toFixed(2) }}</p>
        </div>
        <div class="col-md-6">
          <h3 class="h6">Smoothed Success Rate</h3>
          <p class="mb-0">Last: {{ lastSmoothedSuccess.toFixed(2) }}%</p>
        </div>
      </div>

      <hr class="my-4" />
      <h2 class="h5 mb-2">Training Analysis</h2>
      <p class="text-muted mb-2">
        Early in training, reward curves can fluctuate because the agent explores the environment.
        As training progresses, improved stability and reward trends usually indicate better policy convergence.
        Success rate tracks how often evaluations exceed the success threshold, while standard deviation
        highlights consistency between episodes.
      </p>
      <p class="text-muted mb-0">
        {{ data.points }} evaluations loaded from <code>{{ safeNpzPath }}</code>
      </p>
    </div>

  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { fetchJson } from "../api";

const runs = ref([]);
const selectedRun = ref("");
const maxPoints = ref(30);
const smoothingWindow = ref(5);
const minTimestep = ref(null);
const maxTimestep = ref(null);
const showStdBand = ref(true);
const chartType = ref("smoothed_mean");
const data = ref(null);
const loading = ref(false);
const error = ref("");
const availableMinTimestep = ref(null);
const availableMaxTimestep = ref(null);
const suppressFilterWatch = ref(false);
const lastAutoMinTimestep = ref(null);
const lastAutoMaxTimestep = ref(null);
let debounceTimer;
let requestSequence = 0;

const CHART_WIDTH = 600;
const CHART_HEIGHT = 220;
const CHART_LEFT = 52;
const CHART_RIGHT = 582;
const CHART_TOP = 14;
const CHART_BOTTOM = 188;

const seriesData = computed(() => {
  if (!data.value) return [];
  if (chartType.value === "mean") return data.value.mean_rewards;
  if (chartType.value === "std") return data.value.std_rewards;
  if (chartType.value === "success") return data.value.success_rate;
  return data.value.smoothed_mean;
});

const xAxisSeries = computed(() => {
  if (!data.value) return [];
  if (chartType.value === "smoothed_mean") return data.value.smoothed_timesteps || [];
  return data.value.timesteps || [];
});

const overlayData = computed(() => {
  if (!data.value || chartType.value !== "success") return [];
  return data.value.smoothed_success_rate;
});

function toPolyline(values, min, max) {
  if (!values || values.length < 2) return "";
  const range = max - min || 1;
  return values
    .map((v, i) => {
      const x = CHART_LEFT + (i / (values.length - 1)) * (CHART_RIGHT - CHART_LEFT);
      const y =
        CHART_BOTTOM -
        ((v - min) / range) * (CHART_BOTTOM - CHART_TOP);
      return `${x},${y}`;
    })
    .join(" ");
}

const chartMin = computed(() => {
  const values = seriesData.value || [];
  const overlay = overlayData.value || [];
  const all = [...values, ...overlay];
  return all.length > 0 ? Math.min(...all) : 0;
});

const chartMax = computed(() => {
  const values = seriesData.value || [];
  const overlay = overlayData.value || [];
  const all = [...values, ...overlay];
  return all.length > 0 ? Math.max(...all) : 1;
});

const linePoints = computed(() => {
  return toPolyline(seriesData.value, chartMin.value, chartMax.value);
});

const overlayPoints = computed(() => {
  if (!overlayData.value || overlayData.value.length < 2) return "";
  return toPolyline(overlayData.value, chartMin.value, chartMax.value);
});

const stdBandPoints = computed(() => {
  if (!data.value || chartType.value !== "mean") return "";
  const mean = data.value.mean_rewards;
  const std = data.value.std_rewards;
  if (!mean || mean.length < 2 || !std || std.length !== mean.length) return "";
  const upper = mean.map((v, i) => v + std[i]);
  const lower = mean.map((v, i) => v - std[i]);
  const all = [...upper, ...lower];
  const min = Math.min(...all);
  const max = Math.max(...all);
  const up = toPolyline(upper, min, max);
  const low = toPolyline(lower, min, max)
    .split(" ")
    .reverse()
    .join(" ");
  return `${up} ${low}`;
});

const lineColor = computed(() => {
  if (chartType.value === "std") return "#f39c12";
  if (chartType.value === "success") return "#8e44ad";
  if (chartType.value === "mean") return "#5b46d6";
  return "#0b5d3f";
});

const primaryLabel = computed(() => {
  if (chartType.value === "mean") return "Mean Reward";
  if (chartType.value === "std") return "Reward Standard Deviation";
  if (chartType.value === "success") return "Success Rate";
  return "Smoothed Mean Reward";
});

const primaryLast = computed(() => {
  const values = seriesData.value;
  if (!values || values.length === 0) return 0;
  return values[values.length - 1];
});

const lastSmoothedSuccess = computed(() => {
  if (!data.value || data.value.smoothed_success_rate.length === 0) return 0;
  return data.value.smoothed_success_rate[data.value.smoothed_success_rate.length - 1];
});

function sanitizePath(path) {
  if (!path || typeof path !== "string") return "./runs/unknown/evaluations.npz";
  const normalized = path.replace(/\\/g, "/");
  const runsIndex = normalized.indexOf("/runs/");
  if (runsIndex >= 0) {
    return `.${normalized.slice(runsIndex)}`;
  }
  if (normalized.startsWith("./runs/")) return normalized;
  return "./runs/" + normalized.split("/").filter(Boolean).slice(-3).join("/");
}

const safeNpzPath = computed(() => sanitizePath(data.value?.npz_path));

function formatTick(value) {
  if (!Number.isFinite(value)) return "";
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${(value / 1_000).toFixed(0)}k`;
  if (abs >= 100) return `${Math.round(value)}`;
  return `${value.toFixed(1)}`;
}

const yAxisTicks = computed(() => {
  const min = chartMin.value;
  const max = chartMax.value;
  const steps = 4;
  const range = max - min || 1;
  return Array.from({ length: steps + 1 }, (_, idx) => {
    const ratio = idx / steps;
    const value = max - ratio * range;
    const y = CHART_TOP + ratio * (CHART_BOTTOM - CHART_TOP);
    return { y, label: formatTick(value) };
  });
});

const xAxisTicks = computed(() => {
  const values = xAxisSeries.value;
  if (!values || values.length === 0) return [];
  const min = values[0];
  const max = values[values.length - 1];
  const steps = 4;
  const range = max - min || 1;
  return Array.from({ length: steps + 1 }, (_, idx) => {
    const ratio = idx / steps;
    const value = min + ratio * range;
    const x = CHART_LEFT + ratio * (CHART_RIGHT - CHART_LEFT);
    const anchor = idx === 0 ? "start" : idx === steps ? "end" : "middle";
    return { x, label: formatTick(value), anchor };
  });
});

function normalizeInt(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return null;
  return Math.max(0, Math.trunc(parsed));
}

function syncRangeFromPayload(payload) {
  const hasRunBounds = Number.isFinite(payload?.run_min_timestep) && Number.isFinite(payload?.run_max_timestep);
  if (hasRunBounds) {
    availableMinTimestep.value = payload.run_min_timestep;
    availableMaxTimestep.value = payload.run_max_timestep;
  }

  const timesteps = Array.isArray(payload?.timesteps) ? payload.timesteps : [];
  const fallbackMin = timesteps.length > 0 ? timesteps[0] : null;
  const fallbackMax = timesteps.length > 0 ? timesteps[timesteps.length - 1] : null;
  const nextMin = Number.isFinite(fallbackMin)
    ? fallbackMin
    : (hasRunBounds ? availableMinTimestep.value : null);
  const nextMax = Number.isFinite(fallbackMax)
    ? fallbackMax
    : (hasRunBounds ? availableMaxTimestep.value : null);

  const currentMin = normalizeInt(minTimestep.value);
  const currentMax = normalizeInt(maxTimestep.value);

  const shouldRefreshMin =
    !Number.isFinite(currentMin) ||
    currentMin === lastAutoMinTimestep.value ||
    (Number.isFinite(availableMinTimestep.value) && currentMin < availableMinTimestep.value) ||
    (Number.isFinite(availableMaxTimestep.value) && currentMin > availableMaxTimestep.value);
  const shouldRefreshMax =
    !Number.isFinite(currentMax) ||
    currentMax === lastAutoMaxTimestep.value ||
    (Number.isFinite(availableMaxTimestep.value) && currentMax > availableMaxTimestep.value) ||
    (Number.isFinite(availableMinTimestep.value) && currentMax < availableMinTimestep.value);

  if (shouldRefreshMin || shouldRefreshMax) {
    suppressFilterWatch.value = true;
    if (Number.isFinite(nextMin)) {
      minTimestep.value = nextMin;
      lastAutoMinTimestep.value = nextMin;
    }
    if (Number.isFinite(nextMax)) {
      maxTimestep.value = nextMax;
      lastAutoMaxTimestep.value = nextMax;
    }
    queueMicrotask(() => {
      suppressFilterWatch.value = false;
    });
  }
}

function normalizeField(kind) {
  const current = kind === "min" ? minTimestep.value : maxTimestep.value;
  let next = normalizeInt(current);
  if (!Number.isFinite(next)) {
    return;
  }
  if (Number.isFinite(availableMinTimestep.value)) {
    next = Math.max(next, availableMinTimestep.value);
  }
  if (Number.isFinite(availableMaxTimestep.value)) {
    next = Math.min(next, availableMaxTimestep.value);
  }

  const other = kind === "min" ? normalizeInt(maxTimestep.value) : normalizeInt(minTimestep.value);
  if (Number.isFinite(other)) {
    if (kind === "min" && next > other) next = other;
    if (kind === "max" && next < other) next = other;
  }

  suppressFilterWatch.value = true;
  if (kind === "min") {
    minTimestep.value = next;
  } else {
    maxTimestep.value = next;
  }
  queueMicrotask(() => {
    suppressFilterWatch.value = false;
    scheduleLoad();
  });
}

async function loadRuns() {
  const payload = await fetchJson("/dashboard/runs");
  runs.value = Array.isArray(payload?.runs) ? payload.runs : [];
  if (!selectedRun.value && runs.value.length > 0) {
    selectedRun.value = runs.value[0];
  }
}

async function loadData() {
  if (!selectedRun.value) return;
  const runAtRequest = selectedRun.value;
  const seq = ++requestSequence;
  error.value = "";
  loading.value = true;
  try {
    const normalizedMin = normalizeInt(minTimestep.value);
    const normalizedMax = normalizeInt(maxTimestep.value);

    let requestMin = normalizedMin;
    let requestMax = normalizedMax;
    if (Number.isFinite(requestMin) && Number.isFinite(requestMax) && requestMin > requestMax) {
      requestMin = normalizedMax;
      requestMax = normalizedMin;
    }

    const params = new URLSearchParams();
    params.set("run", runAtRequest);
    params.set("max_points", String(Math.min(30, Math.max(3, Math.trunc(maxPoints.value || 30)))));
    params.set("smoothing_window", String(Math.min(15, Math.max(1, Math.trunc(smoothingWindow.value || 5)))));
    if (Number.isFinite(requestMin)) {
      params.set("min_timestep", String(requestMin));
    }
    if (Number.isFinite(requestMax)) {
      params.set("max_timestep", String(requestMax));
    }
    const payload = await fetchJson(`/dashboard/data?${params.toString()}`);
    if (seq !== requestSequence || runAtRequest !== selectedRun.value) {
      return;
    }
    data.value = payload;
    syncRangeFromPayload(payload);
  } catch (err) {
    if (seq !== requestSequence) {
      return;
    }
    data.value = null;
    error.value = err.message;
  } finally {
    if (seq === requestSequence) {
      loading.value = false;
    }
  }
}

function scheduleLoad() {
  if (debounceTimer) {
    window.clearTimeout(debounceTimer);
  }
  debounceTimer = window.setTimeout(() => {
    loadData();
  }, 250);
}

watch(selectedRun, () => {
  requestSequence += 1;
  suppressFilterWatch.value = true;
  data.value = null;
  error.value = "";
  minTimestep.value = null;
  maxTimestep.value = null;
  lastAutoMinTimestep.value = null;
  lastAutoMaxTimestep.value = null;
  availableMinTimestep.value = null;
  availableMaxTimestep.value = null;
  queueMicrotask(() => {
    suppressFilterWatch.value = false;
  });
  scheduleLoad();
});

watch([maxPoints, smoothingWindow, minTimestep, maxTimestep], () => {
  if (suppressFilterWatch.value) return;
  scheduleLoad();
});

onMounted(async () => {
  try {
    await loadRuns();
    if (selectedRun.value) {
      await loadData();
    }
  } catch (err) {
    error.value = err.message;
  }
});
</script>
