# Public Data Sources

V2 includes a public/open-data layer with official-source metadata and synthetic fallback data. Local values are not live public data.

## Config

Source metadata lives in [config/data_sources.yml](../config/data_sources.yml).

## Source Families

- AHS estimated ED wait times.
- HQCA public aggregate ED metrics.
- Alberta respiratory virus dashboard.
- ECCC/MSC GeoMet weather and alert APIs.
- Alberta AQHI.
- Alberta wildfire maps and data.
- 511 Alberta travel events and road conditions.
- Edmonton/Calgary municipal open traffic and transit data.
- Alberta general holidays and calendar context.
- Non-identifying population/catchment context.

## Local Fallback Cache

Generated cache files live in `data/open/`:

- `facility_reference.csv`
- `public_wait_times.csv`
- `historical_public_ed_metrics.csv`
- `respiratory_surveillance.csv`
- `environmental_stress.csv`
- `travel_friction.csv`
- `calendar_context.csv`
- `population_context.csv`

## Use In The App

Public data supports site-level pressure and scenario context. It must not be interpreted as patient-level source data, and local fallback values must not be reported as official AHS/Government values.
