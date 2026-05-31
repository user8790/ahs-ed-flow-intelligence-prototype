# Research-to-Capability Map

The app now includes this map in the Executive Command Centre. It links research-inspired ideas to concrete app modules, data assets, model outputs, and Snowflake activation paths.

| Research Insight | Implemented Capability | Module Or Component | Data Asset Or Chart | Capability Tier |
| --- | --- | --- | --- | --- |
| Public-data external-pressure forecasting | Hybrid Forecasting Lab | `forecast_external_pressure` | public/open fallback cache | Public prototype |
| Pediatric respiratory surge modelling | Pediatric Respiratory Surge | scenario controls and composite index | `respiratory_surveillance.csv` | Public prototype |
| Weather, smoke, AQHI, wildfire, and heat stress | Environmental stress module | scenario injection and stress score | `environmental_stress.csv` | Public prototype |
| Travel-friction proxy | Travel friction module | road/event/transit/weather proxy | `travel_friction.csv` | Public prototype |
| Scenario workbench combining shocks | Public Scenario Workbench | `ScenarioShockConfig` and `run_combined_public_scenario` | open/synthetic features | Public prototype |
| Probabilistic forecasting | Hybrid Forecasting Lab | P10/P50/P90 ensemble forecast | model validation holdout | Public prototype |
| Forecast-to-simulation pipeline | Simulation Lab | public pressure and scenario outputs feed simulation controls | synthetic `TB_ED_VISITS` | Day-one Snowflake ready |
| Lightweight queue simulation | Simulation Lab | enhanced simulation summary, utilization, occupancy, LWBS hazard | `simulation_feature_tables.sql` | Day-one Snowflake ready |
| Internal-state boundary | Snowflake and lineage tabs | activation status and blockers | `TB_ED_VISITS`, semantic views, operational placeholders | Snowflake |
| Validation discipline | Model Validation and Hybrid Forecasting | holdout metrics, rolling-origin backtest, interval coverage | synthetic/public fallback now, real Snowflake later | Day-one Snowflake ready |
| Operational interpretation | Executive, Scenario, and Simulation tabs | watch-points, levers, pressure-to-action translator, huddle brief | computed output tables | Public and Snowflake |

## Design Principle

The public app forecasts external pressure and demonstrates plausible queue effects. It does not claim to be a true ED digital twin. A true digital twin requires Snowflake access to internal flow timestamps, location events, bed board, staffing, diagnostics, consults, EMS/offload, transfers, and inpatient capacity.
