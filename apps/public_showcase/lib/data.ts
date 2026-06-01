import fs from "node:fs";
import path from "node:path";
import type { Artifact, ShowcaseData } from "./types";

const DATA_DIR = path.join(process.cwd(), "public", "data");

function loadArtifact<T>(fileName: string): Artifact<T> {
  const filePath = path.join(DATA_DIR, fileName);
  return JSON.parse(fs.readFileSync(filePath, "utf8")) as Artifact<T>;
}

export function loadShowcaseData(): ShowcaseData {
  return {
    sites: loadArtifact("sites.json"),
    zones: loadArtifact("zones.json"),
    capabilityMap: loadArtifact("capability_map.json"),
    scenarioResults: loadArtifact("scenario_results_grid.json"),
    simulationBaseline: loadArtifact("simulation_baseline.json"),
    digitalTwin: loadArtifact("synthetic_digital_twin_state.json"),
    validation: loadArtifact("model_validation_summary.json"),
    lineage: loadArtifact("public_lineage_manifest.json"),
    executiveCopy: loadArtifact("executive_demo_copy.json"),
    governance: loadArtifact("governance_boundary.json"),
    researchMap: loadArtifact("research_to_capability_map.json"),
    snowflakeMap: loadArtifact("snowflake_portability_map.json")
  };
}
