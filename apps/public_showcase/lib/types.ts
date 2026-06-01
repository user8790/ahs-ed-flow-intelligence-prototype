export type Artifact<T> = {
  schema_version: string;
  generated_at: string;
  focus_site: string;
  data_mode: string;
  source_type: string;
  synthetic_flag: boolean;
  caveats: string[];
  data: T;
};

export type Signal = {
  signal: string;
  current_value: number;
  display_value: string;
  confidence: string;
  source: string;
  source_type: string;
  refresh_timestamp: string;
  pressure_contribution: number;
  trend: number[];
  why_it_matters: string;
};

export type OpenDataContext = {
  site_context: Record<string, string>;
  signals: Signal[];
  source_chips: Array<{ label: string; freshness: string }>;
  interpretation: string[];
};

export type PublicFact = {
  topic: string;
  classification: string;
  value: string;
  source_title?: string;
  source_url?: string;
  showcase_implication?: string;
};

export type PublicFacts = {
  facts: PublicFact[];
  assumptions: PublicFact[];
  source_urls: Record<string, string>;
};

export type DailyHistoryRow = {
  date: string;
  arrivals: number;
  respiratory_arrivals: number;
  ctas_1_2: number;
  admission_rate: number;
  lwbs_rate: number;
  time_to_physician_mins_p50: number;
  ed_los_discharged_hrs_p50: number;
  ed_los_admitted_hrs_p50: number;
  boarding_hours: number;
  ems_offload_mins_p90: number;
  consult_turnaround_hrs_p50: number;
  respiratory_season_flag: boolean;
  smoke_heat_season_flag: boolean;
  school_in_session_flag: boolean;
};

export type SyntheticHistory = {
  summary: Record<string, number | string>;
  daily: DailyHistoryRow[];
  hourly_profile: Array<Record<string, number>>;
  complaint_mix: Array<{ complaint_group: string; share: number }>;
  age_mix: Array<{ age_band: string; share: number }>;
  arrival_modes: Array<{ mode: string; share: number }>;
  ctas_mix: Array<{ ctas: string; share: number }>;
};

export type CapacityStage = {
  stage: string;
  queue: number;
  occupied: number;
  capacity: number;
  utilization: number;
  pressure: number;
  binding_risk: string;
  operational_note: string;
};

export type CapacityState = {
  snapshot_timestamp: string;
  site: string;
  headline: {
    current_patients_in_ed: number;
    waiting_room_count: number;
    waiting_to_triage: number;
    ctas_1_2_active: number;
    room_occupancy: number;
    boarders: number;
    ems_offload_queue: number;
    physician_queue: number;
    diagnostic_queue: number;
    consult_queue: number;
    expected_admissions_next_12h: number;
    expected_discharges_next_12h: number;
    current_bottleneck: string;
    next_likely_bottleneck: string;
    synthetic_flag: boolean;
  };
  stages: CapacityStage[];
  resource_pools: Array<Record<string, number | string>>;
  bottleneck_timeline: Array<{ hour: string; primary: string; risk: number }>;
  patient_flow_ribbon: Array<{ from: string; to: string; rate_per_hour: number }>;
  synthetic_variation_seed: number;
};

export type UnitCapacity = {
  service: string;
  total_beds_or_planning_capacity: number;
  staffed_beds: number;
  occupied_beds: number;
  pending_discharges: number;
  expected_discharges_4h: number;
  expected_discharges_8h: number;
  expected_discharges_12h: number;
  expected_discharges_24h: number;
  isolation_constraints: number;
  ed_admission_demand_next_12h: number;
  bed_cleaning_queue: number;
  transfer_pressure: number;
  receiving_capacity_risk: number;
  classification: string;
};

export type UnitCapacityData = {
  public_capacity_context: Record<string, number | string>;
  units: UnitCapacity[];
  totals: Record<string, number>;
};

export type BaselineForecastRow = {
  timestamp: string;
  arrivals_p50: number;
  arrivals_p10: number;
  arrivals_p90: number;
  respiratory_arrivals_p50: number;
  ctas_1_2_p50: number;
  ems_arrivals_p50: number;
  interfacility_transfer_p50: number;
  physician_wait_mins_p50: number;
  physician_wait_mins_p10: number;
  physician_wait_mins_p90: number;
  discharged_los_hrs_p50: number;
  admitted_los_hrs_p50: number;
  boarding_hours_p50: number;
  lwbs_risk_p50: number;
  triage_utilization: number;
  room_utilization: number;
  physician_utilization: number;
  inpatient_receiving_utilization: number;
};

export type BaselineSummary = {
  arrivals_72h: number;
  median_physician_wait_mins: number;
  p90_physician_wait_mins: number;
  boarding_hours_72h: number;
  lwbs_risk_peak: number;
  primary_bottleneck: string;
  next_bottleneck: string;
};

export type BaselineForecast = {
  horizon_options: string[];
  baseline_locked: boolean;
  hourly_72h: BaselineForecastRow[];
  daily_28d: Array<Record<string, number | string>>;
  service_bed_demand: Array<Record<string, number | string>>;
  baseline_summary: BaselineSummary;
  model_stack: string[];
  history_anchor: Record<string, number | string>;
};

export type ModelDriver = {
  driver: string;
  importance: number;
  direction: string;
};

export type ModelDrivers = {
  public_drivers: ModelDriver[];
  synthetic_internal_drivers: ModelDriver[];
  confidence: Record<string, string>;
  what_would_improve_confidence: string[];
};

export type ValidationSummary = {
  holdout_window: string;
  holdout_metrics: Array<Record<string, number | string>>;
  calibration: Array<Record<string, number | string>>;
  drift_checks: Array<Record<string, string>>;
  limitations: string[];
};

export type ScenarioControlDefinition = {
  id: keyof ScenarioControls;
  label: string;
  group: string;
  min: number;
  max: number;
  default: number;
  mechanism: string;
  uncertainty_effect: string;
};

export type ScenarioCatalog = {
  groups: Array<{ name: string; control_count: number }>;
  controls: ScenarioControlDefinition[];
};

export type ScenarioControls = Record<string, number>;

export type ScenarioPreset = {
  id: string;
  name: string;
  description: string;
  controls: ScenarioControls;
};

export type ScenarioCoefficients = {
  normalization: string;
  metric_order: string[];
  controls: Record<string, Record<string, number>>;
  nonlinear_rules: string[];
};

export type ScenarioResult = BaselineSummary & {
  uncertainty_width: number;
  effect_vector: Record<string, number>;
};

export type ScenarioDelta = {
  arrivals_72h: number;
  median_physician_wait_mins: number;
  p90_physician_wait_mins: number;
  boarding_hours_72h: number;
  lwbs_risk_peak: number;
};

export type HuddleBriefs = {
  baseline: string[];
  scenarios: Record<string, string[]>;
};

export type UICopy = {
  hero: {
    title: string;
    subtitle: string;
    caveat: string;
  };
  sections: Array<{ id: string; label: string; nav: string }>;
  tone: string;
};

export type ShowcaseData = {
  openDataContext: Artifact<OpenDataContext>;
  publicFacts: Artifact<PublicFacts>;
  history: Artifact<SyntheticHistory>;
  currentState: Artifact<CapacityState>;
  unitCapacity: Artifact<UnitCapacityData>;
  baselineForecast: Artifact<BaselineForecast>;
  modelDrivers: Artifact<ModelDrivers>;
  validationSummary: Artifact<ValidationSummary>;
  scenarioCatalog: Artifact<ScenarioCatalog>;
  scenarioCoefficients: Artifact<ScenarioCoefficients>;
  scenarioPresets: Artifact<ScenarioPreset[]>;
  scenarioResultsGrid: Artifact<Array<Record<string, unknown>>>;
  huddleBriefs: Artifact<HuddleBriefs>;
  uiCopy: Artifact<UICopy>;
};
