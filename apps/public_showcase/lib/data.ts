import fs from "node:fs";
import path from "node:path";
import type {
  Artifact,
  BaselineForecast,
  CapacityState,
  HuddleBriefs,
  ModelDrivers,
  OpenDataContext,
  PublicFacts,
  ScenarioCatalog,
  ScenarioCoefficients,
  ScenarioPreset,
  ShowcaseData,
  SyntheticHistory,
  UICopy,
  UnitCapacityData,
  ValidationSummary
} from "./types";

const DATA_DIR = path.join(process.cwd(), "public", "data");

function fallbackArtifact<T>(fileName: string, data: T): Artifact<T> {
  return {
    schema_version: "fallback",
    generated_at: new Date(0).toISOString(),
    focus_site: "Stollery Children's Hospital",
    data_mode: "fallback",
    source_type: `missing:${fileName}`,
    synthetic_flag: true,
    caveats: ["Artifact missing at build time; fallback shell rendered so the app does not crash."],
    data
  };
}

function loadArtifact<T>(fileName: string, fallback: T): Artifact<T> {
  const filePath = path.join(DATA_DIR, fileName);
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8")) as Artifact<T>;
  } catch {
    return fallbackArtifact(fileName, fallback);
  }
}

export function loadShowcaseData(): ShowcaseData {
  return {
    openDataContext: loadArtifact<OpenDataContext>("stollery_open_data_context.json", {
      site_context: {},
      signals: [],
      source_chips: [],
      interpretation: []
    }),
    publicFacts: loadArtifact<PublicFacts>("stollery_public_facts.json", {
      facts: [],
      assumptions: [],
      source_urls: {}
    }),
    history: loadArtifact<SyntheticHistory>("stollery_synthetic_ed_history.json", {
      summary: {},
      daily: [],
      hourly_profile: [],
      complaint_mix: [],
      age_mix: [],
      arrival_modes: [],
      ctas_mix: []
    }),
    currentState: loadArtifact<CapacityState>("stollery_synthetic_current_state.json", {
      snapshot_timestamp: "",
      site: "Stollery Children's Hospital",
      headline: {
        current_patients_in_ed: 0,
        waiting_room_count: 0,
        waiting_to_triage: 0,
        ctas_1_2_active: 0,
        room_occupancy: 0,
        boarders: 0,
        ems_offload_queue: 0,
        physician_queue: 0,
        diagnostic_queue: 0,
        consult_queue: 0,
        expected_admissions_next_12h: 0,
        expected_discharges_next_12h: 0,
        current_bottleneck: "Unavailable",
        next_likely_bottleneck: "Unavailable",
        synthetic_flag: true
      },
      stages: [],
      resource_pools: [],
      bottleneck_timeline: [],
      patient_flow_ribbon: [],
      synthetic_variation_seed: 0
    }),
    unitCapacity: loadArtifact<UnitCapacityData>("stollery_synthetic_unit_capacity.json", {
      public_capacity_context: {},
      units: [],
      totals: {}
    }),
    baselineForecast: loadArtifact<BaselineForecast>("stollery_forecast_baseline.json", {
      horizon_options: ["24h", "72h", "7d", "28d"],
      baseline_locked: true,
      hourly_72h: [],
      daily_28d: [],
      service_bed_demand: [],
      baseline_summary: {
        arrivals_72h: 0,
        median_physician_wait_mins: 0,
        p90_physician_wait_mins: 0,
        boarding_hours_72h: 0,
        lwbs_risk_peak: 0,
        primary_bottleneck: "Unavailable",
        next_bottleneck: "Unavailable"
      },
      model_stack: [],
      history_anchor: {}
    }),
    modelDrivers: loadArtifact<ModelDrivers>("stollery_model_drivers.json", {
      public_drivers: [],
      synthetic_internal_drivers: [],
      confidence: {},
      what_would_improve_confidence: []
    }),
    validationSummary: loadArtifact<ValidationSummary>("stollery_validation_summary.json", {
      holdout_window: "",
      holdout_metrics: [],
      calibration: [],
      drift_checks: [],
      limitations: []
    }),
    scenarioCatalog: loadArtifact<ScenarioCatalog>("stollery_scenario_catalog.json", {
      groups: [],
      controls: []
    }),
    scenarioCoefficients: loadArtifact<ScenarioCoefficients>("stollery_scenario_coefficients.json", {
      normalization: "",
      metric_order: [],
      controls: {},
      nonlinear_rules: []
    }),
    scenarioPresets: loadArtifact<ScenarioPreset[]>("stollery_scenario_presets.json", []),
    scenarioResultsGrid: loadArtifact<Array<Record<string, unknown>>>("stollery_scenario_results_grid.json", []),
    huddleBriefs: loadArtifact<HuddleBriefs>("stollery_huddle_briefs.json", {
      baseline: [],
      scenarios: {}
    }),
    uiCopy: loadArtifact<UICopy>("stollery_ui_copy.json", {
      hero: {
        title: "Reimagining Alberta ED Flow Intelligence",
        subtitle: "A Stollery-focused public showcase of open-data pressure signals, synthetic operating state, predictive modelling, and scenario-based flow intelligence.",
        caveat: "Public + synthetic demonstration. No real patient data."
      },
      sections: [],
      tone: ""
    })
  };
}
