export type Artifact<T = unknown> = {
  schema_version: string;
  generated_at: string;
  data_mode: string;
  source_categories: string[];
  lineage: Array<Record<string, unknown>>;
  synthetic_flag: boolean;
  caveats: string[];
  payload: T;
};

export type Site = {
  facility: string;
  zone: string;
  city: string;
  peer_group: string;
  pediatric_site: boolean;
  public_pressure_index?: number;
  estimated_wait_mins?: number;
};

export type ShowcaseData = {
  sites: Artifact<Site[]>;
  zones: Artifact<Array<Record<string, unknown>>>;
  capabilityMap: Artifact<Array<Record<string, unknown>>>;
  scenarioResults: Artifact<Record<string, unknown>>;
  simulationBaseline: Artifact<Record<string, unknown>>;
  digitalTwin: Artifact<Record<string, unknown>>;
  validation: Artifact<Record<string, unknown>>;
  lineage: Artifact<Record<string, unknown>>;
  executiveCopy: Artifact<Record<string, unknown>>;
  governance: Artifact<Record<string, unknown>>;
  researchMap: Artifact<Array<Record<string, unknown>>>;
  snowflakeMap: Artifact<Array<Record<string, unknown>>>;
};
