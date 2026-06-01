"use client";

import { useMemo, useState } from "react";
import type {
  BaselineForecastRow,
  CapacityStage,
  DailyHistoryRow,
  ModelDriver,
  ScenarioControlDefinition,
  ScenarioControls,
  ScenarioPreset,
  ShowcaseData,
  Signal,
  UnitCapacity
} from "@/lib/types";
import {
  activeScenarioLabel,
  computeScenarioSummary,
  emptyScenarioControls,
  huddleBrief,
  mergeScenarioControls,
  scenarioDelta,
  scenarioHourlyRows
} from "@/lib/scenarioEngine";

type Horizon = "24h" | "72h" | "7d" | "28d";

function fmtNumber(value: number, digits = 0) {
  return new Intl.NumberFormat("en-CA", { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(value);
}

function fmtPct(value: number, digits = 0) {
  return `${fmtNumber(value * 100, digits)}%`;
}

function signed(value: number, suffix = "") {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${fmtNumber(value, Math.abs(value) < 1 ? 3 : 0)}${suffix}`;
}

function formatRefreshTimestamp(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "timestamp unavailable";
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const hour = String(date.getUTCHours()).padStart(2, "0");
  const minute = String(date.getUTCMinutes()).padStart(2, "0");
  return `${months[date.getUTCMonth()]} ${date.getUTCDate()}, ${hour}:${minute} UTC`;
}

function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "public" | "synthetic" | "scenario" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function Sparkline({ values, color = "#2f7d79" }: { values: number[]; color?: string }) {
  const width = 160;
  const height = 44;
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const points = values
    .map((value, index) => {
      const x = (index / Math.max(1, values.length - 1)) * width;
      const y = height - ((value - min) / Math.max(0.001, max - min)) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg className="sparkline" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Trend sparkline">
      <polyline points={points} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MetricCard({ label, value, detail, tone = "neutral" }: { label: string; value: string; detail: string; tone?: string }) {
  return (
    <article className={`metric-card ${tone}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{detail}</span>
    </article>
  );
}

function DeltaCard({ label, baseline, scenario, delta, suffix = "" }: { label: string; baseline: number; scenario: number; delta: number; suffix?: string }) {
  const improved = delta < 0 && label !== "Arrivals";
  return (
    <article className={`delta-card ${improved ? "improved" : delta > 0 ? "worse" : ""}`}>
      <p>{label}</p>
      <div className="delta-values">
        <span>Baseline <b>{fmtNumber(baseline)}{suffix}</b></span>
        <span>Scenario <b>{fmtNumber(scenario)}{suffix}</b></span>
      </div>
      <strong>{signed(delta, suffix)}</strong>
    </article>
  );
}

function SectionShell({ id, eyebrow, title, intro, children }: { id: string; eyebrow: string; title: string; intro: string; children: React.ReactNode }) {
  return (
    <section id={id} className="major-section">
      <div className="section-heading">
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        <p>{intro}</p>
      </div>
      {children}
    </section>
  );
}

function SignalCard({ signal }: { signal: Signal }) {
  return (
    <article className="signal-card">
      <div>
        <p className="eyebrow">{signal.source_type.replaceAll("_", " ")}</p>
        <h3>{signal.signal}</h3>
      </div>
      <strong>{signal.display_value}</strong>
      <Sparkline values={signal.trend} />
      <div className="bar">
        <span style={{ width: `${Math.round(signal.pressure_contribution * 100)}%` }} />
      </div>
      <p>{signal.why_it_matters}</p>
      <footer>
        <Badge tone={signal.source_type.includes("PUBLIC") ? "public" : "synthetic"}>{signal.confidence} confidence</Badge>
        <small>{formatRefreshTimestamp(signal.refresh_timestamp)}</small>
      </footer>
    </article>
  );
}

function FlowRibbon({ rows }: { rows: Array<{ from: string; to: string; rate_per_hour: number }> }) {
  return (
    <div className="flow-ribbon">
      {rows.map((row, index) => (
        <div className="flow-step" key={`${row.from}-${row.to}`}>
          <i style={{ animationDelay: `${index * 120}ms` }} />
          <span>{row.from}</span>
          <b>{fmtNumber(row.rate_per_hour, 1)}/h</b>
        </div>
      ))}
    </div>
  );
}

function StageBoard({ stages }: { stages: CapacityStage[] }) {
  return (
    <div className="stage-board">
      {stages.map((stage) => (
        <article key={stage.stage} className={`stage-card risk-${stage.binding_risk}`}>
          <div>
            <p>{stage.stage}</p>
            <strong>{stage.queue}</strong>
          </div>
          <span>{stage.occupied}/{stage.capacity} occupied</span>
          <div className="bar">
            <span style={{ width: `${Math.min(100, stage.pressure * 70)}%` }} />
          </div>
          <small>{stage.operational_note}</small>
        </article>
      ))}
    </div>
  );
}

function UnitGrid({ units }: { units: UnitCapacity[] }) {
  return (
    <div className="unit-grid">
      {units.map((unit) => {
        const occupancy = unit.occupied_beds / Math.max(1, unit.staffed_beds);
        return (
          <article key={unit.service} className="unit-card">
            <div>
              <h3>{unit.service}</h3>
              <Badge tone={unit.classification.includes("Public fact") ? "public" : "synthetic"}>{unit.classification}</Badge>
            </div>
            <strong>{unit.occupied_beds}/{unit.staffed_beds}</strong>
            <span>staffed beds occupied</span>
            <div className="bed-dots" aria-label={`${unit.service} bed pressure`}>
              {Array.from({ length: Math.min(24, unit.total_beds_or_planning_capacity) }).map((_, index) => (
                <i key={index} className={index / Math.min(24, unit.total_beds_or_planning_capacity) < occupancy ? "filled" : ""} />
              ))}
            </div>
            <small>{unit.pending_discharges} pending discharges · risk {fmtPct(unit.receiving_capacity_risk, 0)}</small>
          </article>
        );
      })}
    </div>
  );
}

function AreaLineChart({
  baseline,
  scenario,
  mode
}: {
  baseline: Array<{ label: string; p10?: number; p50: number; p90?: number }>;
  scenario: Array<{ label: string; p50: number }>;
  mode: "wait" | "arrivals" | "boarding";
}) {
  const width = 720;
  const height = 260;
  const values = [...baseline.flatMap((row) => [row.p10 ?? row.p50, row.p50, row.p90 ?? row.p50]), ...scenario.map((row) => row.p50)];
  const min = Math.min(...values) * 0.92;
  const max = Math.max(...values) * 1.08;
  const xFor = (index: number, length: number) => (index / Math.max(1, length - 1)) * width;
  const yFor = (value: number) => height - ((value - min) / Math.max(0.001, max - min)) * height;
  const p50 = baseline.map((row, index) => `${xFor(index, baseline.length).toFixed(1)},${yFor(row.p50).toFixed(1)}`).join(" ");
  const scen = scenario.map((row, index) => `${xFor(index, scenario.length).toFixed(1)},${yFor(row.p50).toFixed(1)}`).join(" ");
  const bandTop = baseline.map((row, index) => `${xFor(index, baseline.length).toFixed(1)},${yFor(row.p90 ?? row.p50).toFixed(1)}`).join(" ");
  const bandBottom = [...baseline]
    .reverse()
    .map((row, reverseIndex) => {
      const index = baseline.length - 1 - reverseIndex;
      return `${xFor(index, baseline.length).toFixed(1)},${yFor(row.p10 ?? row.p50).toFixed(1)}`;
    })
    .join(" ");
  return (
    <div className="chart-card">
      <div className="chart-title">
        <h3>{mode === "wait" ? "Physician Wait Forecast" : mode === "arrivals" ? "Demand Forecast" : "Boarding Forecast"}</h3>
        <p>Fixed baseline with dynamic scenario comparator.</p>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${mode} forecast chart`}>
        <polygon points={`${bandTop} ${bandBottom}`} className="forecast-band" />
        <polyline points={p50} className="baseline-line" fill="none" />
        <polyline points={scen} className="scenario-line" fill="none" />
      </svg>
      <div className="legend">
        <span><i className="baseline-dot" /> Baseline P50</span>
        <span><i className="scenario-dot" /> Scenario comparator</span>
        <span><i className="band-dot" /> Baseline P10-P90</span>
      </div>
    </div>
  );
}

function DriverCards({ title, drivers }: { title: string; drivers: ModelDriver[] }) {
  return (
    <div className="driver-panel">
      <h3>{title}</h3>
      {drivers.slice(0, 6).map((driver) => (
        <div className="driver-row" key={driver.driver}>
          <span>{driver.driver}</span>
          <div className="bar">
            <span style={{ width: `${Math.round(driver.importance * 100)}%` }} />
          </div>
          <small>{driver.direction}</small>
        </div>
      ))}
    </div>
  );
}

function ScenarioControl({
  control,
  value,
  onChange
}: {
  control: ScenarioControlDefinition;
  value: number;
  onChange: (id: string, value: number) => void;
}) {
  const isBinary = control.max === 1;
  return (
    <label className="scenario-control">
      <span>
        <b>{control.label}</b>
        <small>{control.mechanism}</small>
      </span>
      {isBinary ? (
        <input type="checkbox" checked={value === 1} onChange={(event) => onChange(control.id, event.target.checked ? 1 : 0)} />
      ) : (
        <>
          <input type="range" min={control.min} max={control.max} value={value} onChange={(event) => onChange(control.id, Number(event.target.value))} />
          <em>{value > 0 ? `+${value}` : value}</em>
        </>
      )}
    </label>
  );
}

function ScenarioStudio({
  controls,
  catalog,
  presets,
  setControls,
  resetControls,
  scenario,
  delta,
  brief
}: {
  controls: ScenarioControls;
  catalog: ScenarioControlDefinition[];
  presets: ScenarioPreset[];
  setControls: (controls: ScenarioControls) => void;
  resetControls: () => void;
  scenario: ReturnType<typeof computeScenarioSummary>;
  delta: ReturnType<typeof scenarioDelta>;
  brief: string[];
}) {
  const [copied, setCopied] = useState(false);
  const grouped = useMemo(() => {
    const map = new Map<string, ScenarioControlDefinition[]>();
    catalog.forEach((control) => {
      map.set(control.group, [...(map.get(control.group) ?? []), control]);
    });
    return Array.from(map.entries());
  }, [catalog]);

  function applyPreset(preset: ScenarioPreset) {
    setControls(mergeScenarioControls(emptyScenarioControls(catalog.map((control) => control.id)), preset.controls));
  }

  async function copyBrief() {
    const text = [`Scenario summary for ${activeScenarioLabel(controls)}`, ...brief].join("\n");
    await navigator.clipboard.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  }

  return (
    <div className="scenario-grid">
      <aside className="preset-panel">
        <div className="panel-heading">
          <h3>Scenario Presets</h3>
          <button className="quiet-button" onClick={resetControls}>Reset baseline</button>
        </div>
        <div className="preset-list">
          {presets.map((preset) => (
            <button key={preset.id} className="preset-card" onClick={() => applyPreset(preset)}>
              <b>{preset.name}</b>
              <span>{preset.description}</span>
            </button>
          ))}
        </div>
      </aside>
      <div className="control-panel">
        <div className="scenario-output">
          <MetricCard label="Scenario pressure" value={scenario.primary_bottleneck} detail={`Uncertainty width ${scenario.uncertainty_width}x`} tone="accent" />
          <MetricCard label="Wait delta" value={signed(delta.median_physician_wait_mins, " min")} detail="median physician initial assessment" />
          <MetricCard label="Boarding delta" value={signed(delta.boarding_hours_72h, " h")} detail="72-hour admitted boarding" />
          <MetricCard label="LWBS risk delta" value={signed(delta.lwbs_risk_peak * 100, " pts")} detail="peak modeled risk" />
        </div>
        <div className="brief-card">
          <div className="panel-heading">
            <h3>Scenario Huddle Brief</h3>
            <button className="quiet-button" onClick={copyBrief}>{copied ? "Copied" : "Copy brief"}</button>
          </div>
          {brief.map((line) => (
            <p key={line}>{line}</p>
          ))}
        </div>
        <div className="control-groups">
          {grouped.map(([group, groupControls], groupIndex) => (
            <details key={group} open={groupIndex < 2}>
              <summary>{group}</summary>
              <div className="control-list">
                {groupControls.map((control) => (
                  <ScenarioControl
                    key={control.id}
                    control={control}
                    value={controls[control.id] ?? 0}
                    onChange={(id, value) => setControls({ ...controls, [id]: value })}
                  />
                ))}
              </div>
            </details>
          ))}
        </div>
      </div>
    </div>
  );
}

function horizonRows(horizon: Horizon, baselineRows: BaselineForecastRow[], scenarioRows: BaselineForecastRow[]) {
  const count = horizon === "24h" ? 24 : 72;
  return {
    baseline: baselineRows.slice(0, count),
    scenario: scenarioRows.slice(0, count)
  };
}

function historyMini(rows: DailyHistoryRow[]) {
  return rows.slice(-90).map((row) => ({ label: row.date.slice(5), p50: row.arrivals }));
}

export function ShowcasePage({ data }: { data: ShowcaseData }) {
  const catalogControls = data.scenarioCatalog.data.controls;
  const baseline = data.baselineForecast.data;
  const [horizon, setHorizon] = useState<Horizon>("72h");
  const [controls, setControls] = useState<ScenarioControls>(() => emptyScenarioControls(catalogControls.map((control) => control.id)));

  const scenario = useMemo(
    () => computeScenarioSummary(baseline.baseline_summary, controls, data.scenarioCoefficients.data),
    [baseline.baseline_summary, controls, data.scenarioCoefficients.data]
  );
  const delta = useMemo(() => scenarioDelta(baseline.baseline_summary, scenario), [baseline.baseline_summary, scenario]);
  const scenarioRows = useMemo(() => scenarioHourlyRows(baseline, controls, data.scenarioCoefficients.data), [baseline, controls, data.scenarioCoefficients.data]);
  const chartRows = horizonRows(horizon, baseline.hourly_72h, scenarioRows);
  const brief = useMemo(() => huddleBrief(baseline.baseline_summary, scenario, delta), [baseline.baseline_summary, scenario, delta]);
  const activeLabel = activeScenarioLabel(controls);
  const isScenarioActive = Object.values(controls).some((value) => value !== 0);

  const arrivalBaseline = horizon === "7d" || horizon === "28d"
    ? baseline.daily_28d.slice(0, horizon === "7d" ? 7 : 28).map((row) => ({
        label: String(row.date),
        p10: Number(row.arrivals_p10),
        p50: Number(row.arrivals_p50),
        p90: Number(row.arrivals_p90)
      }))
    : chartRows.baseline.map((row) => ({ label: row.timestamp, p10: row.arrivals_p10, p50: row.arrivals_p50, p90: row.arrivals_p90 }));
  const arrivalScenario = arrivalBaseline.map((row) => ({
    label: row.label,
    p50: row.p50 * (scenario.arrivals_72h / Math.max(1, baseline.baseline_summary.arrivals_72h))
  }));

  return (
    <main>
      <header className="hero">
        <nav className="top-nav" aria-label="Showcase sections">
          <a href="#open-data">Open Data</a>
          <a href="#synthetic-state">Synthetic ED State</a>
          <a href="#predictive-intelligence">Predictive Intelligence</a>
          <a href="#scenario-studio">Scenario Studio</a>
        </nav>
        <div className="hero-scene" aria-hidden="true">
          {Array.from({ length: 18 }).map((_, index) => (
            <i key={index} style={{ left: `${(index * 7) % 96}%`, animationDelay: `${index * 180}ms` }} />
          ))}
        </div>
        <div className="hero-content">
          <p className="kicker">Stollery Children's Hospital focus</p>
          <h1>{data.uiCopy.data.hero.title}</h1>
          <p className="lede">{data.uiCopy.data.hero.subtitle}</p>
          <div className="hero-actions">
            <select value={horizon} onChange={(event) => setHorizon(event.target.value as Horizon)} aria-label="Forecast horizon">
              {(["24h", "72h", "7d", "28d"] as Horizon[]).map((option) => (
                <option key={option} value={option}>{option} horizon</option>
              ))}
            </select>
            <Badge tone={isScenarioActive ? "scenario" : "neutral"}>{activeLabel}</Badge>
            <Badge tone="synthetic">{data.uiCopy.data.hero.caveat}</Badge>
          </div>
        </div>
        <div className="hero-summary">
          <MetricCard label="Current synthetic ED census" value={String(data.currentState.data.headline.current_patients_in_ed)} detail="patients in ED" />
          <MetricCard label="Public pressure context" value={data.openDataContext.data.signals[0]?.display_value ?? "n/a"} detail="front-door wait proxy" />
          <MetricCard label="Baseline vs scenario" value={signed(delta.median_physician_wait_mins, " min")} detail="median physician wait delta" tone="accent" />
        </div>
      </header>

      <SectionShell
        id="open-data"
        eyebrow="A. Open Data Context"
        title="Public signals that can frame Stollery pressure"
        intro="Open data cannot tell us the internal ED truth. It can, however, provide demand context around respiratory activity, weather, smoke, access friction, calendar effects, and public wait-time signals."
      >
        <div className="signal-grid">
          {data.openDataContext.data.signals.map((signal) => (
            <SignalCard key={signal.signal} signal={signal} />
          ))}
        </div>
        <div className="context-grid">
          <article className="interpretation-panel">
            <h3>Why this matters for Stollery</h3>
            {data.openDataContext.data.interpretation.map((line) => (
              <p key={line}>{line}</p>
            ))}
          </article>
          <article className="facts-panel">
            <h3>Public grounding</h3>
            {data.publicFacts.data.facts.slice(0, 6).map((fact) => (
              <p key={fact.topic}><b>{fact.topic}:</b> {fact.showcase_implication}</p>
            ))}
          </article>
        </div>
      </SectionShell>

      <SectionShell
        id="synthetic-state"
        eyebrow="B. Synthetic Stollery ED Operating Reality"
        title="A realistic pediatric ED operating snapshot"
        intro="This section is synthetic by design. It demonstrates what a governed internal operating layer could show once validated internal feeds are available."
      >
        <div className="status-strip">
          <MetricCard label="Waiting room" value={String(data.currentState.data.headline.waiting_room_count)} detail="synthetic active patients" />
          <MetricCard label="Boarders" value={String(data.currentState.data.headline.boarders)} detail="decision-to-admit patients" />
          <MetricCard label="EMS offload queue" value={String(data.currentState.data.headline.ems_offload_queue)} detail="ambulance handoff proxy" />
          <MetricCard label="Expected admissions" value={String(data.currentState.data.headline.expected_admissions_next_12h)} detail="next 12 hours" />
        </div>
        <FlowRibbon rows={data.currentState.data.patient_flow_ribbon} />
        <StageBoard stages={data.currentState.data.stages} />
        <div className="context-grid">
          <UnitGrid units={data.unitCapacity.data.units} />
          <article className="history-card">
            <h3>Synthetic historical arrival texture</h3>
            <AreaLineChart baseline={historyMini(data.history.data.daily)} scenario={historyMini(data.history.data.daily)} mode="arrivals" />
            <p>{String(data.history.data.summary.synthetic_design)}</p>
          </article>
        </div>
      </SectionShell>

      <SectionShell
        id="predictive-intelligence"
        eyebrow="C. Blended Predictive Intelligence"
        title="Fixed baseline, dynamic scenario comparator"
        intro="Baseline forecasts are generated artifacts and remain unchanged. Scenario overlays are recalculated from the controls in the Scenario Studio."
      >
        <div className="delta-grid">
          <DeltaCard label="Arrivals" baseline={baseline.baseline_summary.arrivals_72h} scenario={scenario.arrivals_72h} delta={delta.arrivals_72h} />
          <DeltaCard label="Median physician wait" baseline={baseline.baseline_summary.median_physician_wait_mins} scenario={scenario.median_physician_wait_mins} delta={delta.median_physician_wait_mins} suffix=" min" />
          <DeltaCard label="P90 physician wait" baseline={baseline.baseline_summary.p90_physician_wait_mins} scenario={scenario.p90_physician_wait_mins} delta={delta.p90_physician_wait_mins} suffix=" min" />
          <DeltaCard label="Boarding hours" baseline={baseline.baseline_summary.boarding_hours_72h} scenario={scenario.boarding_hours_72h} delta={delta.boarding_hours_72h} suffix=" h" />
        </div>
        <div className="charts-grid">
          <AreaLineChart baseline={arrivalBaseline} scenario={arrivalScenario} mode="arrivals" />
          <AreaLineChart
            baseline={chartRows.baseline.map((row) => ({ label: row.timestamp, p10: row.physician_wait_mins_p10, p50: row.physician_wait_mins_p50, p90: row.physician_wait_mins_p90 }))}
            scenario={chartRows.scenario.map((row) => ({ label: row.timestamp, p50: row.physician_wait_mins_p50 }))}
            mode="wait"
          />
          <AreaLineChart
            baseline={chartRows.baseline.map((row) => ({ label: row.timestamp, p50: row.boarding_hours_p50 }))}
            scenario={chartRows.scenario.map((row) => ({ label: row.timestamp, p50: row.boarding_hours_p50 }))}
            mode="boarding"
          />
          <article className="brief-card">
            <h3>Operational Interpretation</h3>
            {brief.map((line) => (
              <p key={line}>{line}</p>
            ))}
          </article>
        </div>
        <div className="context-grid">
          <DriverCards title="Top Public Drivers" drivers={data.modelDrivers.data.public_drivers} />
          <DriverCards title="Top Synthetic Internal Drivers" drivers={data.modelDrivers.data.synthetic_internal_drivers} />
          <article className="validation-panel">
            <h3>Confidence Snapshot</h3>
            {data.validationSummary.data.holdout_metrics.map((row) => (
              <p key={String(row.target)}><b>{String(row.target)}</b> MAE {String(row.mae)} · coverage {fmtPct(Number(row.interval_coverage_p10_p90), 0)}</p>
            ))}
          </article>
        </div>
      </SectionShell>

      <SectionShell
        id="scenario-studio"
        eyebrow="D. Scenario & What-If Studio"
        title="Test interventions before testing workflows"
        intro="Adjust demand shocks, case-mix changes, ED resource levers, inpatient capacity, and workflow options. The comparator changes immediately; baseline stays locked."
      >
        <ScenarioStudio
          controls={controls}
          catalog={catalogControls}
          presets={data.scenarioPresets.data}
          setControls={setControls}
          resetControls={() => setControls(emptyScenarioControls(catalogControls.map((control) => control.id)))}
          scenario={scenario}
          delta={delta}
          brief={brief}
        />
      </SectionShell>

      <footer className="site-footer">
        <p>Public showcase only. Open public references and synthetic demonstration data are used; no real patient data, secure AHS data, private Snowflake data, MRNs, PHNs, ULIs, chart notes, or private endpoints are included.</p>
      </footer>
    </main>
  );
}
