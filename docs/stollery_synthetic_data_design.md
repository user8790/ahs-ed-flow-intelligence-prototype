# Stollery Synthetic Data Design

The rebuild generates Stollery-focused artifacts through:

```powershell
python -m ed_flow_kernel.exports.stollery_public_showcase_export --out apps/public_showcase/public/data --seed 20260601
```

## Design Principles

- Synthetic internal data only.
- Pediatric age bands and CTAS mix are explicitly represented.
- Time-of-day, weekend, school calendar, respiratory season, smoke/heat season, and boarding effects shape the synthetic history.
- Unit capacity is grounded by public total-capacity context where available and labelled as synthetic where not public.
- Scenario outputs are deterministic and derived from coefficients, not random browser changes.

## Generated Artifacts

- `stollery_open_data_context.json`
- `stollery_public_facts.json`
- `stollery_synthetic_ed_history.json`
- `stollery_synthetic_current_state.json`
- `stollery_synthetic_unit_capacity.json`
- `stollery_forecast_baseline.json`
- `stollery_model_drivers.json`
- `stollery_validation_summary.json`
- `stollery_scenario_catalog.json`
- `stollery_scenario_coefficients.json`
- `stollery_scenario_presets.json`
- `stollery_scenario_results_grid.json`
- `stollery_huddle_briefs.json`
- `stollery_ui_copy.json`

## Synthetic History

The exporter creates 24 months of daily synthetic ED operating history with:

- arrivals
- respiratory arrivals
- CTAS 1-2 volume
- admission rate
- LWBS rate
- physician initial assessment wait
- discharged and admitted LOS
- boarding hours
- EMS offload p90
- consult turnaround
- respiratory, smoke/heat, and school flags

## Current Snapshot

The current-state artifact includes queues, stage occupancy, resource pools, patient-flow ribbon, and bottleneck timeline. It is intended to make the demo feel operationally concrete while remaining public-safe.

## Capacity Assumptions

The unit grid uses a 236-bed public context from public planning material. Service-level staffed beds, occupancy, pending discharges, bed cleaning, and capacity risk are synthetic planning assumptions.
