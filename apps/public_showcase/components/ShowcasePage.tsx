import type { ShowcaseData, Site } from "@/lib/types";

function pct(value: unknown) {
  const num = Number(value ?? 0);
  return `${Math.round(num * 100)}%`;
}

function metric(value: unknown, suffix = "") {
  const num = Number(value ?? 0);
  if (Number.isNaN(num)) return "n/a";
  return `${Math.round(num)}${suffix}`;
}

function Card({ title, value, caption }: { title: string; value: string; caption: string }) {
  return (
    <article className="card">
      <p className="eyebrow">{title}</p>
      <strong>{value}</strong>
      <span>{caption}</span>
    </article>
  );
}

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="section">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function MiniBars({ rows, valueKey }: { rows: Array<Record<string, unknown>>; valueKey: string }) {
  return (
    <div className="bars">
      {rows.slice(0, 7).map((row, index) => {
        const label = String(row.facility ?? row.zone ?? row.resource_pool ?? row.research_insight ?? `Item ${index + 1}`);
        const value = Math.max(0.04, Number(row[valueKey] ?? row.utilization_index ?? 0));
        return (
          <div className="bar-row" key={`${label}-${index}`}>
            <span>{label}</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${Math.min(100, value * 100)}%` }} />
            </div>
            <b>{pct(value)}</b>
          </div>
        );
      })}
    </div>
  );
}

function TwinCanvas({ data }: { data: ShowcaseData }) {
  const twin = data.digitalTwin.payload;
  const utilization = Array.isArray(twin.resource_utilization) ? (twin.resource_utilization as Array<Record<string, unknown>>) : [];
  const nodes = ["community", "arrival", "triage", "waiting", "rooming", "physician", "diagnostics", "consults", "disposition", "boarding", "bed"];
  return (
    <div className="twin">
      <div className="flowline">
        {nodes.map((node, index) => (
          <div className="flow-node" key={node}>
            <i style={{ animationDelay: `${index * 90}ms` }} />
            <span>{node}</span>
          </div>
        ))}
      </div>
      <MiniBars rows={utilization} valueKey="utilization_index" />
    </div>
  );
}

export function ShowcasePage({ data }: { data: ShowcaseData }) {
  const sites = data.sites.payload as Site[];
  const topSites = [...sites].sort((a, b) => Number(b.public_pressure_index ?? 0) - Number(a.public_pressure_index ?? 0)).slice(0, 4);
  const scenario = data.scenarioResults.payload;
  const impact = Array.isArray(scenario.impact) ? (scenario.impact as Array<Record<string, unknown>>) : [];
  const huddle = Array.isArray(scenario.huddle) ? (scenario.huddle as string[]) : [];
  const simulation = data.simulationBaseline.payload;
  const simHuddle = Array.isArray(simulation.huddle) ? (simulation.huddle as string[]) : [];
  const validation = data.validation.payload;
  const modelRows = Array.isArray(validation.holdout_validation) ? (validation.holdout_validation as Array<Record<string, unknown>>) : [];
  const governance = data.governance.payload as Record<string, unknown>;

  return (
    <main>
      <header className="hero">
        <nav>
          <a href="#cockpit">Cockpit</a>
          <a href="#scenario">Scenario Theatre</a>
          <a href="#twin">Digital Twin</a>
          <a href="#snowflake">Snowflake</a>
          <a href="#lineage">Lineage</a>
        </nav>
        <div className="hero-grid">
          <div>
            <p className="kicker">SAO Advisory public showcase</p>
            <h1>Reimagining Alberta ED Flow Intelligence</h1>
            <p className="lede">From public pressure signals to secure operational intelligence.</p>
            <div className="chips">
              <span>Open-data-shaped</span>
              <span>Synthetic future-state</span>
              <span>No patient data</span>
              <span>Snowflake-portable kernel</span>
            </div>
          </div>
          <div className="hero-panel">
            <p>Capability ladder</p>
            {data.capabilityMap.payload.map((row, index) => (
              <div className="ladder" key={String(row.tier)}>
                <b>{index + 1}</b>
                <span>{String(row.tier)}</span>
              </div>
            ))}
          </div>
        </div>
      </header>

      <Section id="cockpit" title="Alberta Pressure Cockpit">
        <div className="cards">
          {topSites.map((site) => (
            <Card key={site.facility} title={site.facility} value={pct(site.public_pressure_index)} caption={`${site.zone} · wait signal ${metric(site.estimated_wait_mins, " min")}`} />
          ))}
        </div>
        <MiniBars rows={sites as unknown as Array<Record<string, unknown>>} valueKey="public_pressure_index" />
      </Section>

      <Section id="scenario" title="Scenario Theatre">
        <div className="split">
          <div>
            <p className="body-copy">A combined respiratory, smoke, travel, and synthetic capacity shock is translated into operational watch-points. Numerical effects come from exported kernel artifacts, not from browser-side reinvention.</p>
            <div className="cards compact">
              {impact.slice(0, 4).map((row) => (
                <Card key={String(row.metric)} title={String(row.metric)} value={String(row.change_label)} caption={String(row.operational_interpretation)} />
              ))}
            </div>
          </div>
          <div className="huddle">
            <h3>Capacity huddle brief</h3>
            {huddle.map((line) => (
              <p key={line}>{line}</p>
            ))}
          </div>
        </div>
      </Section>

      <Section id="twin" title="Future Digital Twin Canvas">
        <p className="body-copy">Synthetic future-state demonstration: community demand propagates through arrivals, triage, rooms, physician assessment, diagnostics, consults, disposition, boarding, inpatient beds, and discharge or transfer.</p>
        <TwinCanvas data={data} />
      </Section>

      <Section id="respiratory" title="Pediatric Respiratory Surge Story">
        <div className="split">
          <MiniBars rows={data.researchMap.payload.slice(0, 8)} valueKey="synthetic_score" />
          <div className="huddle">
            <h3>Why it matters</h3>
            <p>Stollery Children’s Hospital and Alberta Children’s Hospital are represented as pediatric focus sites in the public artifact layer.</p>
            <p>Respiratory, school calendar, smoke, and access signals become richer once joined to governed internal Snowflake features.</p>
          </div>
        </div>
      </Section>

      <Section id="snowflake" title="Snowflake Portability Story">
        <div className="architecture">
          {data.snowflakeMap.payload.map((row) => (
            <article key={String(row.component)}>
              <h3>{String(row.component)}</h3>
              <p><b>Local:</b> {String(row.local_mode)}</p>
              <p><b>Snowflake:</b> {String(row.snowflake_mode)}</p>
            </article>
          ))}
        </div>
      </Section>

      <Section id="lineage" title="Data Lineage and Trust">
        <div className="split">
          <div>
            <p className="body-copy">Every JSON artifact carries schema version, generation time, lineage, source categories, synthetic flag, and caveats. Public artifacts exclude patient-level data and secure AHS data.</p>
            <div className="chips">
              {data.lineage.source_categories.map((category) => (
                <span key={category}>{category}</span>
              ))}
            </div>
          </div>
          <div className="huddle">
            <h3>Governance boundary</h3>
            {Array.isArray(governance.huddle_brief) ? governance.huddle_brief.map((line) => <p key={String(line)}>{String(line)}</p>) : null}
          </div>
        </div>
      </Section>

      <Section id="research-map" title="Research-to-Capability Map">
        <div className="table">
          {data.researchMap.payload.slice(0, 9).map((row) => (
            <div className="table-row" key={String(row.research_insight)}>
              <b>{String(row.research_insight)}</b>
              <span>{String(row.implemented_capability)}</span>
              <em>{String(row.capability_tier)}</em>
            </div>
          ))}
        </div>
      </Section>

      <Section id="validation" title="Validation Posture">
        <div className="cards compact">
          {modelRows.slice(0, 4).map((row) => (
            <Card key={String(row.model)} title={String(row.model)} value={metric(row.mae)} caption={`RMSE ${metric(row.rmse)} · WAPE ${pct(row.wape)}`} />
          ))}
        </div>
        <div className="huddle">
          <h3>Simulation huddle sample</h3>
          {simHuddle.map((line) => (
            <p key={line}>{line}</p>
          ))}
        </div>
      </Section>

      <footer>
        <p>Public/synthetic demonstration only. Secure AHS data, identifiers, and chart context remain outside this public surface.</p>
      </footer>
    </main>
  );
}
