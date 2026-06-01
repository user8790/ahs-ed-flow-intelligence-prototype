import type {
  BaselineForecast,
  BaselineForecastRow,
  BaselineSummary,
  ScenarioCoefficients,
  ScenarioControls,
  ScenarioDelta,
  ScenarioResult
} from "./types";

const BINARY_CONTROLS = new Set([
  "respiratorySurgePathway",
  "extendFastTrack",
  "rapidAssessmentProvider",
  "pullToFull",
  "physicianInTriage",
  "earlyBedHuddle",
  "dischargeBeforeNoon",
  "consultantResponseTarget",
  "diagnosticPrioritization",
  "temporaryFlexSpace"
]);

type EffectVector = Record<string, number>;

const EFFECT_KEYS = [
  "demand",
  "respiratory",
  "ctas12",
  "wait",
  "los",
  "boarding",
  "lwbs",
  "roomUtilization",
  "physicianUtilization",
  "inpatientUtilization",
  "ems",
  "isolation",
  "frontDoor",
  "uncertainty"
];

function clip(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function round(value: number, digits = 1) {
  const scale = 10 ** digits;
  return Math.round(value * scale) / scale;
}

function effectVector(controls: ScenarioControls, coefficients: ScenarioCoefficients): EffectVector {
  const effects = Object.fromEntries(EFFECT_KEYS.map((key) => [key, 0])) as EffectVector;
  Object.entries(controls).forEach(([controlId, rawValue]) => {
    const coeffs = coefficients.controls[controlId] ?? {};
    const value = BINARY_CONTROLS.has(controlId) ? rawValue : rawValue / 100;
    Object.entries(coeffs).forEach(([effect, coeff]) => {
      effects[effect] = (effects[effect] ?? 0) + coeff * value;
    });
  });
  return effects;
}

export function emptyScenarioControls(controlIds: string[]): ScenarioControls {
  return Object.fromEntries(controlIds.map((id) => [id, 0]));
}

export function mergeScenarioControls(base: ScenarioControls, patch: ScenarioControls): ScenarioControls {
  return { ...base, ...patch };
}

export function computeScenarioSummary(
  baseline: BaselineSummary,
  controls: ScenarioControls,
  coefficients: ScenarioCoefficients
): ScenarioResult {
  const effects = effectVector(controls, coefficients);
  const stress = Math.max(0, effects.demand + effects.ctas12 + effects.boarding + effects.isolation * 0.35);
  const waitMultiplier = Math.max(
    0.5,
    1 + effects.wait + effects.demand * 0.85 + effects.ctas12 * 0.55 + Math.max(0, effects.boarding) * 0.38 + effects.isolation * 0.18
  );
  const boardingMultiplier = Math.max(0.42, 1 + effects.boarding + effects.demand * 0.25 + effects.ctas12 * 0.2 + effects.isolation * 0.12);
  const p90Multiplier = waitMultiplier * (1 + Math.max(0, effects.uncertainty) * 0.6 + stress * 0.08);
  const arrivals = baseline.arrivals_72h * Math.max(0.72, 1 + effects.demand);
  const medianWait = baseline.median_physician_wait_mins * waitMultiplier;
  const p90Wait = baseline.p90_physician_wait_mins * p90Multiplier;
  const boarding = baseline.boarding_hours_72h * boardingMultiplier;
  const lwbs = clip(baseline.lwbs_risk_peak * (1 + effects.lwbs + Math.max(0, medianWait - 180) / 500), 0.005, 0.18);

  return {
    arrivals_72h: round(arrivals, 1),
    median_physician_wait_mins: round(medianWait, 1),
    p90_physician_wait_mins: round(p90Wait, 1),
    boarding_hours_72h: round(boarding, 1),
    lwbs_risk_peak: round(lwbs, 3),
    primary_bottleneck: bottleneckName(effects, medianWait, boarding),
    next_bottleneck: effects.boarding < -0.08 ? "Physician initial assessment" : "Rooming and inpatient receiving",
    uncertainty_width: round(1 + Math.max(0, effects.uncertainty) + stress * 0.35, 2),
    effect_vector: Object.fromEntries(Object.entries(effects).map(([key, value]) => [key, round(value, 3)]))
  };
}

export function scenarioDelta(baseline: BaselineSummary, scenario: ScenarioResult): ScenarioDelta {
  return {
    arrivals_72h: round(scenario.arrivals_72h - baseline.arrivals_72h, 1),
    median_physician_wait_mins: round(scenario.median_physician_wait_mins - baseline.median_physician_wait_mins, 1),
    p90_physician_wait_mins: round(scenario.p90_physician_wait_mins - baseline.p90_physician_wait_mins, 1),
    boarding_hours_72h: round(scenario.boarding_hours_72h - baseline.boarding_hours_72h, 1),
    lwbs_risk_peak: round(scenario.lwbs_risk_peak - baseline.lwbs_risk_peak, 3)
  };
}

export function scenarioHourlyRows(
  forecast: BaselineForecast,
  controls: ScenarioControls,
  coefficients: ScenarioCoefficients
): BaselineForecastRow[] {
  const effects = effectVector(controls, coefficients);
  const waitMultiplier = Math.max(
    0.5,
    1 + effects.wait + effects.demand * 0.85 + effects.ctas12 * 0.55 + Math.max(0, effects.boarding) * 0.38 + effects.isolation * 0.18
  );
  const boardingMultiplier = Math.max(0.42, 1 + effects.boarding + effects.demand * 0.25 + effects.ctas12 * 0.2 + effects.isolation * 0.12);
  const uncertainty = Math.max(0.72, 1 + Math.max(0, effects.uncertainty));
  return forecast.hourly_72h.map((row, index) => {
    const eveningDamping = index % 24 > 16 ? 1 + Math.max(0, effects.demand) * 0.2 : 1;
    const arrivals = row.arrivals_p50 * Math.max(0.72, 1 + effects.demand) * eveningDamping;
    const wait = row.physician_wait_mins_p50 * waitMultiplier;
    const p90 = row.physician_wait_mins_p90 * waitMultiplier * uncertainty;
    const boarding = row.boarding_hours_p50 * boardingMultiplier;
    return {
      ...row,
      arrivals_p50: round(arrivals, 2),
      arrivals_p10: round(arrivals * 0.78, 2),
      arrivals_p90: round(arrivals * 1.24 * uncertainty, 2),
      respiratory_arrivals_p50: round(row.respiratory_arrivals_p50 * Math.max(0.65, 1 + effects.respiratory + effects.demand * 0.45), 2),
      ctas_1_2_p50: round(row.ctas_1_2_p50 * Math.max(0.7, 1 + effects.ctas12), 2),
      ems_arrivals_p50: round(row.ems_arrivals_p50 * Math.max(0.7, 1 + effects.ems + effects.demand * 0.2), 2),
      physician_wait_mins_p50: round(wait, 1),
      physician_wait_mins_p10: round(wait * 0.72, 1),
      physician_wait_mins_p90: round(p90, 1),
      discharged_los_hrs_p50: round(row.discharged_los_hrs_p50 * Math.max(0.72, 1 + effects.los + effects.wait * 0.22), 2),
      admitted_los_hrs_p50: round(row.admitted_los_hrs_p50 * Math.max(0.68, 1 + effects.los + effects.boarding * 0.34), 2),
      boarding_hours_p50: round(boarding, 2),
      lwbs_risk_p50: round(clip(row.lwbs_risk_p50 * (1 + effects.lwbs + Math.max(0, wait - 180) / 500), 0.005, 0.18), 3),
      room_utilization: round(clip(row.room_utilization + effects.roomUtilization + Math.max(0, effects.boarding) * 0.12, 0.2, 1.5), 2),
      physician_utilization: round(clip(row.physician_utilization + effects.physicianUtilization + Math.max(0, effects.wait) * 0.15, 0.2, 1.5), 2),
      inpatient_receiving_utilization: round(clip(row.inpatient_receiving_utilization + effects.inpatientUtilization + Math.max(0, effects.boarding) * 0.18, 0.2, 1.5), 2)
    };
  });
}

export function activeScenarioLabel(controls: ScenarioControls) {
  const active = Object.entries(controls).filter(([, value]) => value !== 0);
  if (active.length === 0) return "Baseline comparator";
  return `${active.length} active scenario lever${active.length === 1 ? "" : "s"}`;
}

export function huddleBrief(baseline: BaselineSummary, scenario: ScenarioResult, delta: ScenarioDelta) {
  const improved = delta.median_physician_wait_mins < -5 || delta.boarding_hours_72h < -50;
  return [
    improved ? "Scenario appears to relieve one measurable flow constraint." : "Scenario adds or leaves meaningful flow pressure in place.",
    `Physician wait changes by ${delta.median_physician_wait_mins > 0 ? "+" : ""}${Math.round(delta.median_physician_wait_mins)} minutes; boarding changes by ${delta.boarding_hours_72h > 0 ? "+" : ""}${Math.round(delta.boarding_hours_72h)} hours over 72 hours.`,
    `Baseline bottleneck is ${baseline.primary_bottleneck}; scenario bottleneck reads as ${scenario.primary_bottleneck}.`,
    scenario.primary_bottleneck.includes("Inpatient") ? "Watch bed release timing, bed cleaning, and specialty receiving capacity over the next 4-12 hours." : "Watch room pull, physician initial assessment, and diagnostic turnaround over the next 4-12 hours.",
    "This interpretation is public-demo logic and would need real-time staffing, acuity, diagnostics, consult, and bed-board validation."
  ];
}

function bottleneckName(effects: EffectVector, wait: number, boarding: number) {
  if (boarding > 1100 || effects.boarding > 0.06 || effects.inpatientUtilization > 0.06) return "Inpatient receiving capacity";
  if (wait > 210 || effects.wait > 0.05) return "Physician initial assessment";
  if (effects.roomUtilization > 0.05) return "Rooming capacity";
  if (effects.los > 0.08) return "Diagnostics and consult turnaround";
  return "Rooming and diagnostics";
}
