# Stollery Scenario Engine

The public showcase uses a deterministic browser-side scenario engine at:

`apps/public_showcase/lib/scenarioEngine.ts`

## State Model

- Baseline forecast artifacts load once and remain fixed.
- Scenario controls are stored in React state.
- Presets patch control state.
- Reset returns every control to baseline.
- Comparator rows and summary metrics are recalculated from coefficients.

## Control Groups

The scenario catalog includes:

- External Demand Shocks
- Case-Mix and Acuity Shocks
- ED Resource Levers
- Inpatient and System Levers
- Operational Workflow Options

## Comparator Logic

Controls map to effect vectors:

- demand
- respiratory
- CTAS 1-2 acuity
- physician wait
- LOS
- boarding
- LWBS hazard
- room utilization
- physician utilization
- inpatient utilization
- EMS/access
- isolation
- uncertainty

The engine applies nonlinear rules:

- severe shocks widen uncertainty;
- wait and LWBS rise faster after high physician-wait pressure;
- inpatient constraints can dampen upstream interventions;
- boarding reduction can reveal physician assessment or rooming as the next bottleneck.

## Output

The engine produces:

- scenario summary
- scenario deltas
- comparator hourly forecast rows
- bottleneck shift
- huddle brief

This is public-demo logic. Real deployment would need calibrated coefficients, model replay, and governance review.
