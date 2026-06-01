# Stollery Public Facts And Synthetic Assumptions

Updated: 2026-06-01

The public showcase is Stollery-only. It uses public facts where credible public sources exist and labels internal operating values as synthetic planning assumptions.

## Public Facts Used

| Topic | Classification | Source |
| --- | --- | --- |
| Pediatric ED role and central/northern Alberta referral context | Public fact | AHS Emergency Department, Pediatric service listing: https://www.albertahealthservices.ca/findhealth/Service.aspx?id=1067772&serviceAtFacilityID=1105308 |
| Stollery ED location, 24-hour service, and age eligibility | Public fact | AHS Emergency Department, Pediatric service listing: https://www.albertahealthservices.ca/findhealth/Service.aspx?id=1067772&serviceAtFacilityID=1105308 |
| Stollery ED workflow: triage first, then registration and either bed or waiting room | Public fact | AHS Stollery Emergency Department page: https://www.albertahealthservices.ca/stollery/page14037.aspx |
| AHS estimated ED wait-time definition | Public fact | AHS estimated emergency department wait times: https://www.albertahealthservices.ca/waittimes/waittimes.aspx |
| Weekly Edmonton ED LOS reporting includes Stollery | Public fact | AHS weekly Edmonton ED LOS summary: https://www.albertahealthservices.ca/assets/about/data/ahs-data-er-wait-times-edmonton.pdf |
| Stollery public total bed context and broad site split from 2021 planning material | Public fact | Stollery Foundation stand-alone hospital article: https://www.stollerykids.com/media-centre/exploring-a-new-stand-alone-childrens-hospital/ |
| Hiller PICU 16-room public context | Public fact | Stollery Foundation Hiller PICU article: https://www.stollerykids.com/media-centre/new-stollery-picu/ |
| Alberta respiratory virus dashboard context | Public fact | Government of Alberta respiratory virus dashboard: https://www.alberta.ca/stats/dashboard/respiratory-virus-dashboard.htm?data=data-notes |
| Edmonton AQHI/weather context | Public fact | Environment Canada Edmonton AQHI: https://weather.gc.ca/airquality/pages/abaq-001_e.html |
| Road/access context | Public fact | 511 Alberta API documentation: https://511.alberta.ca/developers/doc |

## Synthetic Planning Assumptions

- Current ED census, queues, waits, boarders, utilization, bottlenecks, and scenario impacts are synthetic.
- Unit/service-level staffed beds are rounded planning assumptions unless directly supported by public source material.
- The unit grid is constrained to the public total-capacity context but should not be interpreted as current Stollery staffed-bed truth.
- Forecasts and model validation are deterministic synthetic demonstrations, not operational performance claims.
- Public wait-time context is represented as a fallback-calibrated signal because the showcase does not store or scrape live AHS operational values.

## Public Fact Versus Demo Value

The UI uses badges:

- `Public fact`: cited public reference.
- `Synthetic assumption`: plausible operating assumption calibrated to public context.
- `Demo-only`: invented demonstration output for product behavior.

No precise public fact is created where only broad public evidence exists.
