"""Export Stollery-focused public-safe artifacts for the Vercel showcase."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from ed_flow_kernel.governance.privacy import public_payload_has_phi_like_values


FOCUS_SITE = "Stollery Children's Hospital"
GENERATED_AT = "2026-06-01T12:00:00+00:00"
SCHEMA_VERSION = "2.0"

ARTIFACT_NAMES = [
    "stollery_open_data_context.json",
    "stollery_public_facts.json",
    "stollery_synthetic_ed_history.json",
    "stollery_synthetic_current_state.json",
    "stollery_synthetic_unit_capacity.json",
    "stollery_forecast_baseline.json",
    "stollery_model_drivers.json",
    "stollery_validation_summary.json",
    "stollery_scenario_catalog.json",
    "stollery_scenario_coefficients.json",
    "stollery_scenario_presets.json",
    "stollery_scenario_results_grid.json",
    "stollery_huddle_briefs.json",
    "stollery_ui_copy.json",
]


PUBLIC_SOURCES = {
    "ahs_pediatric_ed": "https://www.albertahealthservices.ca/findhealth/Service.aspx?id=1067772&serviceAtFacilityID=1105308",
    "ahs_stollery_ed": "https://www.albertahealthservices.ca/stollery/page14037.aspx",
    "ahs_wait_times": "https://www.albertahealthservices.ca/waittimes/waittimes.aspx",
    "ahs_weekly_ed_los": "https://www.albertahealthservices.ca/assets/about/data/ahs-data-er-wait-times-edmonton.pdf",
    "stollery_beds": "https://www.stollerykids.com/media-centre/exploring-a-new-stand-alone-childrens-hospital/",
    "stollery_picu": "https://www.stollerykids.com/media-centre/new-stollery-picu/",
    "alberta_respiratory_dashboard": "https://www.alberta.ca/stats/dashboard/respiratory-virus-dashboard.htm?data=data-notes",
    "edmonton_aqhi": "https://weather.gc.ca/airquality/pages/abaq-001_e.html",
    "alberta_511": "https://511.alberta.ca/developers/doc",
}


def export_stollery_public_showcase_artifacts(out: str | Path, seed: int = 20260601, mode: str = "public_demo") -> list[Path]:
    """Generate all Stollery public-showcase artifacts."""

    rng = np.random.default_rng(seed)
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    public_facts = _public_facts()
    open_context = _open_data_context(rng)
    history = _synthetic_history(rng)
    current_state = _current_state(rng)
    unit_capacity = _unit_capacity(rng)
    baseline = _baseline_forecast(rng, history, current_state, unit_capacity)
    drivers = _model_drivers()
    validation = _validation_summary()
    catalog = _scenario_catalog()
    coefficients = _scenario_coefficients()
    presets = _scenario_presets()
    grid = _scenario_results_grid(baseline, current_state, unit_capacity, coefficients, presets)
    briefs = _huddle_briefs(grid)
    ui_copy = _ui_copy()

    artifacts = {
        "stollery_open_data_context.json": ("mixed_public_cached_and_synthetic_fallback", "OPEN_AND_SYNTHETIC_CONTEXT", open_context),
        "stollery_public_facts.json": ("public_references_and_assumptions", "PUBLIC_FACTS", public_facts),
        "stollery_synthetic_ed_history.json": ("synthetic_internal_operating_history", "SYNTHETIC_INTERNAL", history),
        "stollery_synthetic_current_state.json": ("synthetic_current_ed_snapshot", "SYNTHETIC_INTERNAL", current_state),
        "stollery_synthetic_unit_capacity.json": ("synthetic_unit_capacity_with_public_context", "PUBLIC_FACTS_PLUS_SYNTHETIC_ASSUMPTIONS", unit_capacity),
        "stollery_forecast_baseline.json": ("synthetic_model_output", "MODEL_OUTPUT", baseline),
        "stollery_model_drivers.json": ("synthetic_model_summary", "MODEL_OUTPUT", drivers),
        "stollery_validation_summary.json": ("synthetic_validation_summary", "MODEL_VALIDATION_DEMO", validation),
        "stollery_scenario_catalog.json": ("scenario_control_contract", "SCENARIO_DEFINITION", catalog),
        "stollery_scenario_coefficients.json": ("scenario_engine_contract", "SCENARIO_ENGINE", coefficients),
        "stollery_scenario_presets.json": ("scenario_preset_contract", "SCENARIO_DEFINITION", presets),
        "stollery_scenario_results_grid.json": ("precomputed_preset_results", "MODEL_OUTPUT", grid),
        "stollery_huddle_briefs.json": ("deterministic_interpretation", "INTERPRETATION", briefs),
        "stollery_ui_copy.json": ("public_showcase_copy", "COPY", ui_copy),
    }

    written: list[Path] = []
    for name in ARTIFACT_NAMES:
        data_mode, source_type, data = artifacts[name]
        artifact = _envelope(data_mode=data_mode, source_type=source_type, data=data)
        if public_payload_has_phi_like_values(artifact):
            raise ValueError(f"Artifact {name} appears to contain PHI-like content.")
        path = out_dir / name
        path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(path)
    return written


def _envelope(*, data_mode: str, source_type: str, data: Any) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": GENERATED_AT,
        "focus_site": FOCUS_SITE,
        "data_mode": data_mode,
        "source_type": source_type,
        "synthetic_flag": True,
        "caveats": [
            "Public showcase only. No real patient data, secure AHS data, private Snowflake data, or private AHS endpoints are used.",
            "Internal ED operating state, model outputs, scenario effects, and unit-level operating values are synthetic demonstration values.",
            "Public facts are used only where cited. Unit-level values without public evidence are labelled synthetic planning assumptions.",
        ],
        "data": data,
    }


def _public_facts() -> dict[str, Any]:
    facts = [
        {
            "topic": "Pediatric ED role",
            "classification": "Public fact",
            "value": "The Stollery pediatric emergency department is described by AHS as the only specialized ED and referral centre for children in central and northern Alberta.",
            "source_title": "AHS Emergency Department, Pediatric service listing",
            "source_url": PUBLIC_SOURCES["ahs_pediatric_ed"],
            "showcase_implication": "The public demo is Stollery-only and pediatric-referral oriented.",
        },
        {
            "topic": "Location",
            "classification": "Public fact",
            "value": "8440 112 Street, Edmonton, Alberta.",
            "source_title": "AHS Emergency Department, Pediatric service listing",
            "source_url": PUBLIC_SOURCES["ahs_pediatric_ed"],
            "showcase_implication": "Open-data context focuses on Edmonton weather, access, AQHI, and Edmonton Zone ED signals.",
        },
        {
            "topic": "Service hours",
            "classification": "Public fact",
            "value": "24-hour pediatric emergency service.",
            "source_title": "AHS Emergency Department, Pediatric service listing",
            "source_url": PUBLIC_SOURCES["ahs_pediatric_ed"],
            "showcase_implication": "Forecasts use continuous hourly demand and staffing assumptions.",
        },
        {
            "topic": "Eligibility",
            "classification": "Public fact",
            "value": "Children from birth up to their 18th birthday.",
            "source_title": "AHS Emergency Department, Pediatric service listing",
            "source_url": PUBLIC_SOURCES["ahs_pediatric_ed"],
            "showcase_implication": "Synthetic age bands use newborn, neonate, infant, toddler, child, and adolescent cohorts.",
        },
        {
            "topic": "Wait-time definition",
            "classification": "Public fact",
            "value": "AHS estimated ED wait times represent time from triage assessment to physician assessment, not total hospital time.",
            "source_title": "AHS estimated emergency department wait times",
            "source_url": PUBLIC_SOURCES["ahs_wait_times"],
            "showcase_implication": "The public wait-time signal is shown as a front-door physician-wait proxy, not ED LOS.",
        },
        {
            "topic": "Triage workflow",
            "classification": "Public fact",
            "value": "The Stollery ED page says the first person families meet is a triage nurse, followed by registration and either a bed or the waiting room.",
            "source_title": "AHS Stollery emergency department page",
            "source_url": PUBLIC_SOURCES["ahs_stollery_ed"],
            "showcase_implication": "The synthetic flow board starts with triage, registration, waiting, rooming, and physician assessment.",
        },
        {
            "topic": "Hospital bed context",
            "classification": "Public fact",
            "value": "A public Stollery Foundation article described the Stollery as operating 236 beds across sites in 2021 planning material.",
            "source_title": "Stollery Foundation stand-alone children's hospital article",
            "source_url": PUBLIC_SOURCES["stollery_beds"],
            "showcase_implication": "The unit grid uses 236 as public total-capacity context, while many service splits remain synthetic assumptions.",
        },
        {
            "topic": "Broad public bed split",
            "classification": "Public fact",
            "value": "The same public article listed 161 beds at Walter C. Mackenzie Health Sciences Centre, 69 neonatal intensive care beds at the Royal Alexandra site, and 6 intensive care beds at the Sturgeon Community Hospital NICU.",
            "source_title": "Stollery Foundation stand-alone children's hospital article",
            "source_url": PUBLIC_SOURCES["stollery_beds"],
            "showcase_implication": "The synthetic bed grid avoids claiming unsupported exact unit splits beyond this broad public context.",
        },
        {
            "topic": "PICU room context",
            "classification": "Public fact",
            "value": "The Hiller PICU public article described 16 single-family rooms and noted a previous 12-bed open unit with four beds added in 2017.",
            "source_title": "Stollery Foundation Hiller PICU article",
            "source_url": PUBLIC_SOURCES["stollery_picu"],
            "showcase_implication": "PICU capacity is represented as a public-fact anchor while operating occupancy remains synthetic.",
        },
        {
            "topic": "ED performance reporting",
            "classification": "Public fact",
            "value": "AHS publishes a weekly Edmonton ED length-of-stay summary that includes Stollery Children's Hospital.",
            "source_title": "AHS Weekly Emergency Department Length of Stay Summary - Edmonton",
            "source_url": PUBLIC_SOURCES["ahs_weekly_ed_los"],
            "showcase_implication": "Historical public performance context is represented as an open signal, not secure visit-level truth.",
        },
        {
            "topic": "Respiratory surveillance",
            "classification": "Public fact",
            "value": "Alberta publishes an aggregate respiratory virus dashboard covering viruses such as RSV, influenza, COVID-19, hMPV, parainfluenza, rhinovirus/enterovirus and others.",
            "source_title": "Government of Alberta respiratory virus dashboard",
            "source_url": PUBLIC_SOURCES["alberta_respiratory_dashboard"],
            "showcase_implication": "Respiratory pressure is a public driver blended with synthetic pediatric ED history.",
        },
        {
            "topic": "Edmonton AQHI",
            "classification": "Public fact",
            "value": "Environment Canada publishes Edmonton Air Quality Health Index observations and forecasts.",
            "source_title": "Environment Canada Edmonton AQHI",
            "source_url": PUBLIC_SOURCES["edmonton_aqhi"],
            "showcase_implication": "Smoke and air-quality stress are represented as pediatric respiratory demand modifiers.",
        },
        {
            "topic": "Road/access events",
            "classification": "Public fact",
            "value": "511 Alberta provides road conditions, events, alerts, weather stations, and related API documentation.",
            "source_title": "511 Alberta API documentation",
            "source_url": PUBLIC_SOURCES["alberta_511"],
            "showcase_implication": "Travel/access friction is treated as a proxy for arrival timing and EMS offload variation, not an EMS feed.",
        },
    ]
    assumptions = [
        {
            "topic": "Unit-level staffed beds",
            "classification": "Synthetic planning assumption",
            "value": "Specific current staffed-bed counts by pediatric service are not asserted as public facts. They are rounded synthetic planning values constrained to public total-capacity context.",
        },
        {
            "topic": "Current ED state",
            "classification": "Demo-only invented value",
            "value": "Current queues, wait times, boarders, resource utilization, and bottleneck calls are synthetic and regenerated deterministically from the export seed.",
        },
        {
            "topic": "Forecast and scenario outputs",
            "classification": "Demo-only invented value",
            "value": "Forecasts and scenario effects are synthetic model demonstrations intended to show product behavior, not operational truth.",
        },
    ]
    return {"facts": facts, "assumptions": assumptions, "source_urls": PUBLIC_SOURCES}


def _open_data_context(rng: np.random.Generator) -> dict[str, Any]:
    now = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    signal_specs = [
        ("Public ED wait-time signal", 0.61, "AHS estimated ED wait-time concept; demo value is fallback-calibrated", "PUBLIC_WITH_SYNTHETIC_FALLBACK", "Moderate-high front-door pressure"),
        ("Respiratory activity", 0.47, "Alberta respiratory virus surveillance context", "PUBLIC_CONTEXT_SYNTHETIC_VALUE", "Off-season but pediatric respiratory sensitivity remains relevant"),
        ("School/calendar effect", 0.34, "School calendar and holiday seasonality proxy", "CALENDAR_DERIVED", "Routine school-week demand pattern"),
        ("Weather and AQHI", 0.42, "Environment Canada Edmonton AQHI/weather context", "PUBLIC_CONTEXT_SYNTHETIC_VALUE", "Air-quality and temperature effects are watch signals"),
        ("Smoke and wildfire stress", 0.38, "Summer smoke season proxy", "PUBLIC_CONTEXT_SYNTHETIC_VALUE", "Respiratory/asthma presentations could rise if AQHI worsens"),
        ("Travel/access friction", 0.53, "511 Alberta road/events proxy", "PUBLIC_CONTEXT_SYNTHETIC_VALUE", "Arrival timing and transfer logistics may become lumpier"),
        ("Public events", 0.29, "Edmonton event/calendar proxy", "SYNTHETIC_FALLBACK", "Minor injury and access timing sensitivity"),
    ]
    signals: list[dict[str, Any]] = []
    for index, (name, baseline, source, source_type, interpretation) in enumerate(signal_specs):
        trend = []
        for hour in range(36):
            wave = math.sin((hour + index * 3) / 5.0) * 0.07
            noise = rng.normal(0, 0.018)
            trend.append(round(float(np.clip(baseline + wave + noise, 0.05, 0.95)), 3))
        signals.append(
            {
                "signal": name,
                "current_value": round(float(np.clip(trend[-1], 0.05, 0.95)), 3),
                "display_value": _signal_display(name, trend[-1]),
                "confidence": ["High", "Medium", "Medium", "Medium", "Medium", "Medium", "Low"][index],
                "source": source,
                "source_type": source_type,
                "refresh_timestamp": (now - timedelta(minutes=18 + index * 7)).isoformat(),
                "pressure_contribution": round(float(np.clip(baseline * (0.82 + index * 0.035), 0.03, 0.9)), 3),
                "trend": trend,
                "why_it_matters": interpretation,
            }
        )
    return {
        "site_context": {
            "facility": FOCUS_SITE,
            "city": "Edmonton",
            "zone": "Edmonton Zone",
            "role": "Specialized pediatric ED and referral centre for central and northern Alberta",
            "public_plus_synthetic_note": "Open public signals are blended with synthetic fallback values for a public demo.",
        },
        "signals": signals,
        "source_chips": [
            {"label": "AHS wait-time concept", "freshness": "public page available; live value not stored"},
            {"label": "AHS weekly ED LOS PDF", "freshness": "public weekly reporting"},
            {"label": "Alberta respiratory dashboard", "freshness": "public aggregate surveillance"},
            {"label": "Environment Canada AQHI", "freshness": "public observations/forecast"},
            {"label": "511 Alberta", "freshness": "public road/access API"},
        ],
        "interpretation": [
            "The public pressure layer is strongest for travel/access friction and front-door wait context.",
            "Respiratory context is below winter peak but remains a pediatric demand driver.",
            "AQHI and smoke are watch signals because children with respiratory vulnerability can cluster quickly.",
        ],
    }


def _signal_display(name: str, value: float) -> str:
    if "wait" in name.lower():
        return f"{round(80 + value * 95)} min"
    if "AQHI" in name or "Weather" in name:
        return f"{round(1 + value * 7)} AQHI-equivalent"
    return f"{round(value * 100)}%"


def _synthetic_history(rng: np.random.Generator) -> dict[str, Any]:
    start = datetime(2024, 6, 1, tzinfo=timezone.utc)
    daily = []
    hourly_profile = []
    for day in range(731):
        dt = start + timedelta(days=day)
        dow = dt.weekday()
        winter = 1.0 + 0.23 * max(0, math.cos((dt.timetuple().tm_yday - 20) / 365 * 2 * math.pi))
        school = 1.08 if dt.month in {9, 10, 11, 1, 2, 3} else 0.97
        weekend = 1.08 if dow in {5, 6} else 1.0
        smoke = 1.0 + (0.08 if dt.month in {6, 7, 8} else 0)
        base_arrivals = 142 * winter * school * weekend * smoke
        arrivals = int(max(85, rng.normal(base_arrivals, 14)))
        respiratory = int(arrivals * np.clip(0.18 + (winter - 1) * 0.42 + rng.normal(0, 0.025), 0.08, 0.42))
        ctas12 = int(arrivals * np.clip(0.13 + rng.normal(0, 0.015), 0.08, 0.2))
        admission_rate = float(np.clip(0.18 + respiratory / max(arrivals, 1) * 0.11 + rng.normal(0, 0.015), 0.12, 0.31))
        admitted = int(arrivals * admission_rate)
        lwbs = float(np.clip(0.018 + max(0, arrivals - 155) * 0.0009 + rng.normal(0, 0.004), 0.006, 0.075))
        physician_wait = float(np.clip(96 + (arrivals - 130) * 1.45 + admitted * 0.9 + rng.normal(0, 18), 32, 340))
        los_discharged = float(np.clip(4.1 + physician_wait / 160 + rng.normal(0, 0.35), 2.2, 8.9))
        boarding = float(np.clip(admitted * (0.9 + rng.normal(0, 0.18)), 7, 64))
        daily.append(
            {
                "date": dt.date().isoformat(),
                "arrivals": arrivals,
                "respiratory_arrivals": respiratory,
                "ctas_1_2": ctas12,
                "admission_rate": round(admission_rate, 3),
                "lwbs_rate": round(lwbs, 3),
                "time_to_physician_mins_p50": round(physician_wait, 1),
                "ed_los_discharged_hrs_p50": round(los_discharged, 2),
                "ed_los_admitted_hrs_p50": round(los_discharged + 3.1 + boarding / 35, 2),
                "boarding_hours": round(boarding, 1),
                "ems_offload_mins_p90": round(26 + max(0, arrivals - 140) * 0.28 + rng.normal(0, 5), 1),
                "consult_turnaround_hrs_p50": round(1.7 + admitted * 0.012 + rng.normal(0, 0.18), 2),
                "respiratory_season_flag": dt.month in {10, 11, 12, 1, 2, 3},
                "smoke_heat_season_flag": dt.month in {6, 7, 8},
                "school_in_session_flag": dt.month in {1, 2, 3, 4, 5, 9, 10, 11, 12},
            }
        )
    complaint_mix = [
        {"complaint_group": "respiratory", "share": 0.23},
        {"complaint_group": "fever/infectious", "share": 0.16},
        {"complaint_group": "GI/dehydration", "share": 0.1},
        {"complaint_group": "injury/trauma", "share": 0.18},
        {"complaint_group": "mental health", "share": 0.07},
        {"complaint_group": "neurologic", "share": 0.06},
        {"complaint_group": "abdominal pain", "share": 0.08},
        {"complaint_group": "endocrine/metabolic", "share": 0.04},
        {"complaint_group": "oncology/immunocompromised", "share": 0.03},
        {"complaint_group": "other", "share": 0.05},
    ]
    for dow in range(7):
        for hour in range(24):
            evening = 1 + 0.45 * math.exp(-((hour - 18) ** 2) / 26)
            overnight = 0.58 + 0.18 * math.exp(-((hour - 2) ** 2) / 12)
            weekend = 1.1 if dow in {5, 6} else 1
            hourly_profile.append(
                {
                    "day_of_week": dow,
                    "hour": hour,
                    "expected_arrivals": round(5.7 * evening * overnight * weekend, 2),
                    "respiratory_share": round(0.18 + 0.04 * math.cos((hour - 20) / 24 * 2 * math.pi), 3),
                    "ems_share": round(0.1 + 0.02 * (1 if hour < 7 else 0), 3),
                }
            )
    return {
        "summary": {
            "history_start": daily[0]["date"],
            "history_end": daily[-1]["date"],
            "days": len(daily),
            "mean_daily_arrivals": round(float(np.mean([row["arrivals"] for row in daily])), 1),
            "mean_admission_rate": round(float(np.mean([row["admission_rate"] for row in daily])), 3),
            "synthetic_design": "24 months of deterministic synthetic pediatric ED history with respiratory, school, smoke, weekend, and boarding effects.",
        },
        "daily": daily,
        "hourly_profile": hourly_profile,
        "complaint_mix": complaint_mix,
        "age_mix": [
            {"age_band": "newborn", "share": 0.03},
            {"age_band": "neonate", "share": 0.04},
            {"age_band": "infant", "share": 0.14},
            {"age_band": "toddler", "share": 0.19},
            {"age_band": "child", "share": 0.36},
            {"age_band": "adolescent", "share": 0.24},
        ],
        "arrival_modes": [
            {"mode": "walk-in/private vehicle", "share": 0.72},
            {"mode": "EMS", "share": 0.11},
            {"mode": "interfacility transfer", "share": 0.09},
            {"mode": "clinic referral", "share": 0.08},
        ],
        "ctas_mix": [
            {"ctas": "1", "share": 0.015},
            {"ctas": "2", "share": 0.115},
            {"ctas": "3", "share": 0.43},
            {"ctas": "4", "share": 0.34},
            {"ctas": "5", "share": 0.10},
        ],
    }


def _current_state(rng: np.random.Generator) -> dict[str, Any]:
    stages = [
        ("waiting-to-triage", 3, 7, 2, "front-door triage smoothing"),
        ("triaged waiting", 18, 42, 16, "waiting-room and room availability"),
        ("roomed not yet seen", 7, 48, 8, "physician initial assessment"),
        ("physician assessment queue", 13, 11, 9, "provider coverage and acuity mix"),
        ("diagnostics queue", 15, 12, 8, "lab/imaging turnaround"),
        ("consult queue", 9, 7, 6, "specialty response and admission-likely cases"),
        ("disposition pending", 12, 10, 7, "decision-making and discharge execution"),
        ("admitted boarding", 19, 16, 15, "inpatient receiving capacity"),
        ("transfer pending", 4, 3, 2, "interfacility logistics"),
        ("discharge pending", 11, 9, 5, "family readiness and final orders"),
    ]
    stage_rows = []
    for name, queue, occupied, capacity, note in stages:
        utilization = occupied / max(capacity, 1)
        stage_rows.append(
            {
                "stage": name,
                "queue": queue,
                "occupied": occupied,
                "capacity": capacity,
                "utilization": round(utilization, 2),
                "pressure": round(float(np.clip(queue / 20 + utilization * 0.45, 0, 1.5)), 2),
                "binding_risk": "high" if utilization > 1.05 or queue > 16 else "moderate" if queue > 8 else "watch",
                "operational_note": note,
            }
        )
    return {
        "snapshot_timestamp": "2026-06-01T12:00:00-06:00",
        "site": FOCUS_SITE,
        "headline": {
            "current_patients_in_ed": 119,
            "waiting_room_count": 42,
            "waiting_to_triage": 7,
            "ctas_1_2_active": 15,
            "room_occupancy": 0.92,
            "boarders": 19,
            "ems_offload_queue": 4,
            "physician_queue": 13,
            "diagnostic_queue": 15,
            "consult_queue": 9,
            "expected_admissions_next_12h": 18,
            "expected_discharges_next_12h": 44,
            "current_bottleneck": "Inpatient receiving capacity and ED boarding",
            "next_likely_bottleneck": "Physician initial assessment if arrivals rise after 16:00",
            "synthetic_flag": True,
        },
        "stages": stage_rows,
        "resource_pools": [
            {"resource": "triage nurses", "baseline_capacity": 4, "current_capacity": 3, "utilization": 0.88, "label": "synthetic planning assumption"},
            {"resource": "treatment rooms", "baseline_capacity": 48, "current_capacity": 45, "utilization": 0.92, "label": "synthetic planning assumption"},
            {"resource": "resuscitation/critical spaces", "baseline_capacity": 8, "current_capacity": 7, "utilization": 0.86, "label": "synthetic planning assumption"},
            {"resource": "fast-track spaces", "baseline_capacity": 8, "current_capacity": 6, "utilization": 0.74, "label": "synthetic planning assumption"},
            {"resource": "respiratory cohort spaces", "baseline_capacity": 12, "current_capacity": 11, "utilization": 0.96, "label": "synthetic planning assumption"},
            {"resource": "physician coverage", "baseline_capacity": 7, "current_capacity": 6, "utilization": 0.91, "label": "synthetic planning assumption"},
            {"resource": "diagnostic throughput", "baseline_capacity": 1.0, "current_capacity": 0.86, "utilization": 0.89, "label": "abstract synthetic capacity"},
            {"resource": "consult throughput", "baseline_capacity": 1.0, "current_capacity": 0.82, "utilization": 0.94, "label": "abstract synthetic capacity"},
            {"resource": "EMS offload bays", "baseline_capacity": 5, "current_capacity": 4, "utilization": 0.81, "label": "synthetic planning assumption"},
        ],
        "bottleneck_timeline": [
            {"hour": "12:00", "primary": "boarding", "risk": 0.84},
            {"hour": "14:00", "primary": "boarding", "risk": 0.82},
            {"hour": "16:00", "primary": "physician assessment", "risk": 0.78},
            {"hour": "18:00", "primary": "rooming", "risk": 0.76},
            {"hour": "20:00", "primary": "diagnostics", "risk": 0.68},
            {"hour": "22:00", "primary": "boarding", "risk": 0.73},
            {"hour": "00:00", "primary": "boarding", "risk": 0.8},
        ],
        "patient_flow_ribbon": [
            {"from": "arrival", "to": "triage", "rate_per_hour": 6.8},
            {"from": "triage", "to": "waiting", "rate_per_hour": 5.9},
            {"from": "waiting", "to": "rooming", "rate_per_hour": 4.6},
            {"from": "rooming", "to": "physician", "rate_per_hour": 4.4},
            {"from": "physician", "to": "diagnostics/consult", "rate_per_hour": 3.8},
            {"from": "disposition", "to": "discharge", "rate_per_hour": 3.2},
            {"from": "decision-to-admit", "to": "inpatient bed", "rate_per_hour": 1.2},
        ],
        "synthetic_variation_seed": int(rng.integers(1000, 9999)),
    }


def _unit_capacity(rng: np.random.Generator) -> dict[str, Any]:
    units = [
        ("General Pediatrics", 42, "Synthetic planning assumption", 0.91),
        ("Pediatric Medicine / Hospital Pediatrics", 26, "Synthetic planning assumption", 0.93),
        ("Pediatric Surgery", 18, "Synthetic planning assumption", 0.88),
        ("Pediatric Oncology / Hematology", 14, "Synthetic planning assumption", 0.86),
        ("Mental Health / Child & Adolescent", 6, "Synthetic planning assumption", 0.96),
        ("Short Stay / Observation", 7, "Synthetic planning assumption", 0.81),
        ("Pediatric ICU", 16, "Public fact anchored; operating state synthetic", 0.94),
        ("Pediatric Cardiology / Cardiac ICU", 16, "Synthetic planning assumption", 0.9),
        ("Other critical care / transport stabilization", 16, "Synthetic planning assumption", 0.82),
        ("Neonatal / NICU context across Stollery sites", 75, "Public fact anchored; operating state synthetic", 0.89),
    ]
    rows = []
    for idx, (service, beds, classification, occ_rate) in enumerate(units):
        staffed = max(1, round(beds * (0.88 + (idx % 3) * 0.035)))
        occupied = min(staffed + 2, max(0, round(staffed * occ_rate)))
        pending = int(max(0, rng.poisson(1 + beds / 24)))
        rows.append(
            {
                "service": service,
                "total_beds_or_planning_capacity": beds,
                "staffed_beds": staffed,
                "occupied_beds": occupied,
                "pending_discharges": pending,
                "expected_discharges_4h": max(0, pending - 1),
                "expected_discharges_8h": pending + int(idx % 2),
                "expected_discharges_12h": pending + int(idx % 3),
                "expected_discharges_24h": pending + 2 + int(idx % 4),
                "isolation_constraints": round(float(np.clip(0.16 + (idx % 4) * 0.07 + rng.normal(0, 0.02), 0.05, 0.55)), 2),
                "ed_admission_demand_next_12h": round(float(np.clip(1.3 + beds / 22 + rng.normal(0, 0.3), 0.3, 8.5)), 1),
                "bed_cleaning_queue": int(max(0, rng.poisson(1.2))),
                "transfer_pressure": round(float(np.clip(0.18 + (idx % 5) * 0.08 + rng.normal(0, 0.02), 0.05, 0.75)), 2),
                "receiving_capacity_risk": round(float(np.clip(occupied / max(staffed, 1) + (0.1 if pending < 2 else -0.03), 0.2, 1.25)), 2),
                "classification": classification,
            }
        )
    return {
        "public_capacity_context": {
            "public_total_beds_context": 236,
            "public_broad_split_note": "Public 2021 planning material described 161 beds at Walter C. Mackenzie, 69 NICU beds at Royal Alexandra, and 6 NICU beds at Sturgeon. Current service-level operating values below are synthetic.",
            "source_url": PUBLIC_SOURCES["stollery_beds"],
        },
        "units": rows,
        "totals": {
            "total_capacity_rows": sum(row["total_beds_or_planning_capacity"] for row in rows),
            "staffed_beds": sum(row["staffed_beds"] for row in rows),
            "occupied_beds": sum(row["occupied_beds"] for row in rows),
            "pending_discharges": sum(row["pending_discharges"] for row in rows),
            "expected_discharges_24h": sum(row["expected_discharges_24h"] for row in rows),
        },
    }


def _baseline_forecast(
    rng: np.random.Generator,
    history: dict[str, Any],
    current_state: dict[str, Any],
    unit_capacity: dict[str, Any],
) -> dict[str, Any]:
    hourly = []
    base_time = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    for hour in range(72):
        ts = base_time + timedelta(hours=hour)
        day_factor = 1 + (0.08 if ts.weekday() in {5, 6} else 0)
        evening = 1 + 0.42 * math.exp(-((ts.hour - 18) ** 2) / 24)
        respiratory_wave = 0.22 + 0.04 * math.sin((hour + 6) / 12)
        arrivals = 5.5 * day_factor * evening + rng.normal(0, 0.25)
        wait = 92 + hour * 0.45 + arrivals * 9.5 + current_state["headline"]["boarders"] * 1.6
        boarding = 12.5 + current_state["headline"]["boarders"] * 0.42 + math.sin(hour / 7) * 2
        row = {
            "timestamp": ts.isoformat(),
            "arrivals_p50": round(float(arrivals), 2),
            "arrivals_p10": round(float(arrivals * 0.78), 2),
            "arrivals_p90": round(float(arrivals * 1.26), 2),
            "respiratory_arrivals_p50": round(float(arrivals * respiratory_wave), 2),
            "ctas_1_2_p50": round(float(arrivals * 0.13), 2),
            "ems_arrivals_p50": round(float(arrivals * 0.11), 2),
            "interfacility_transfer_p50": round(float(arrivals * 0.08), 2),
            "physician_wait_mins_p50": round(float(wait), 1),
            "physician_wait_mins_p10": round(float(wait * 0.72), 1),
            "physician_wait_mins_p90": round(float(wait * 1.42), 1),
            "discharged_los_hrs_p50": round(float(3.7 + wait / 165), 2),
            "admitted_los_hrs_p50": round(float(7.2 + boarding / 4.2), 2),
            "boarding_hours_p50": round(float(boarding), 2),
            "lwbs_risk_p50": round(float(np.clip(0.018 + wait / 5600, 0.01, 0.1)), 3),
            "triage_utilization": round(float(np.clip(0.68 + arrivals / 16, 0.35, 1.25)), 2),
            "room_utilization": round(float(np.clip(0.76 + arrivals / 22 + boarding / 100, 0.35, 1.35)), 2),
            "physician_utilization": round(float(np.clip(0.7 + wait / 480, 0.4, 1.35)), 2),
            "inpatient_receiving_utilization": round(float(np.clip(0.78 + boarding / 55, 0.4, 1.3)), 2),
        }
        hourly.append(row)
    daily = []
    for day in range(28):
        rows = hourly[(day % 3) * 24 : (day % 3) * 24 + 24]
        if len(rows) < 24:
            rows = hourly[:24]
        total = sum(row["arrivals_p50"] for row in rows) * (1 + 0.03 * math.sin(day / 3))
        daily.append(
            {
                "date": (base_time + timedelta(days=day)).date().isoformat(),
                "arrivals_p50": round(total, 1),
                "arrivals_p10": round(total * 0.86, 1),
                "arrivals_p90": round(total * 1.17, 1),
                "respiratory_arrivals_p50": round(total * (0.21 + 0.03 * math.sin(day / 5)), 1),
                "expected_admissions_p50": round(total * 0.2, 1),
                "expected_boarding_hours_p50": round(34 + day * 0.3 + 7 * math.sin(day / 4), 1),
            }
        )
    service_demand = [
        {
            "service": row["service"],
            "baseline_demand_next_24h": round(float(row["ed_admission_demand_next_12h"] * 1.85), 1),
            "bed_availability_next_24h": row["expected_discharges_24h"] + max(0, row["staffed_beds"] - row["occupied_beds"]),
            "constraint_risk": row["receiving_capacity_risk"],
        }
        for row in unit_capacity["units"]
    ]
    return {
        "horizon_options": ["24h", "72h", "7d", "28d"],
        "baseline_locked": True,
        "hourly_72h": hourly,
        "daily_28d": daily,
        "service_bed_demand": service_demand,
        "baseline_summary": {
            "arrivals_72h": round(sum(row["arrivals_p50"] for row in hourly), 1),
            "median_physician_wait_mins": round(float(np.median([row["physician_wait_mins_p50"] for row in hourly])), 1),
            "p90_physician_wait_mins": round(float(np.percentile([row["physician_wait_mins_p90"] for row in hourly], 90)), 1),
            "boarding_hours_72h": round(sum(row["boarding_hours_p50"] for row in hourly), 1),
            "lwbs_risk_peak": round(float(max(row["lwbs_risk_p50"] for row in hourly)), 3),
            "primary_bottleneck": "Inpatient receiving capacity",
            "next_bottleneck": "Physician initial assessment",
        },
        "model_stack": [
            "seasonal naive baseline",
            "moving average baseline",
            "regularized regression-style adjustment",
            "tree-style nonlinear modifier",
            "bootstrap interval wrapper",
            "deterministic scenario adjustment engine",
        ],
        "history_anchor": history["summary"],
    }


def _model_drivers() -> dict[str, Any]:
    return {
        "public_drivers": [
            {"driver": "respiratory activity", "importance": 0.84, "direction": "higher increases arrivals and respiratory cohort demand"},
            {"driver": "school calendar", "importance": 0.71, "direction": "school weeks increase infectious and injury timing"},
            {"driver": "weather/AQHI/smoke", "importance": 0.67, "direction": "smoke and cold shift respiratory and asthma load"},
            {"driver": "traffic/access", "importance": 0.58, "direction": "access friction clusters arrivals and transfer delays"},
            {"driver": "holiday/events", "importance": 0.43, "direction": "holidays and events change time-of-day arrival shape"},
        ],
        "synthetic_internal_drivers": [
            {"driver": "current queue", "importance": 0.88, "direction": "front-door backlog raises wait and LWBS risk"},
            {"driver": "CTAS mix", "importance": 0.82, "direction": "higher acuity consumes room, physician, diagnostic, and critical-care resources"},
            {"driver": "room occupancy", "importance": 0.77, "direction": "limits pull from waiting room"},
            {"driver": "physician utilization", "importance": 0.74, "direction": "raises time to initial assessment"},
            {"driver": "inpatient receiving capacity", "importance": 0.91, "direction": "drives boarding and admitted LOS"},
            {"driver": "pending discharges", "importance": 0.66, "direction": "bed availability timing relieves boarding"},
            {"driver": "boarding hours", "importance": 0.86, "direction": "ties up rooms and shifts bottleneck upstream"},
        ],
        "confidence": {
            "demand_forecast": "medium-high in synthetic validation",
            "wait_forecast": "medium; sensitive to current queues and staffing",
            "boarding_forecast": "medium-low; needs real ADT and bed-board validation",
            "scenario_effects": "directional demonstration only",
        },
        "what_would_improve_confidence": [
            "real-time ED location and queue timestamps",
            "validated staffed-bed and pending-discharge feeds",
            "diagnostic and consult turnaround feeds",
            "holdout replay by season and facility",
        ],
    }


def _validation_summary() -> dict[str, Any]:
    return {
        "holdout_window": "synthetic 2026-03-01 to 2026-05-31",
        "holdout_metrics": [
            {"target": "daily arrivals", "mae": 9.8, "mape": 0.067, "interval_coverage_p10_p90": 0.82},
            {"target": "respiratory arrivals", "mae": 4.1, "mape": 0.118, "interval_coverage_p10_p90": 0.79},
            {"target": "physician wait", "mae": 24.5, "mape": 0.154, "interval_coverage_p10_p90": 0.77},
            {"target": "boarding hours", "mae": 8.9, "mape": 0.191, "interval_coverage_p10_p90": 0.74},
            {"target": "LWBS risk", "mae": 0.008, "mape": 0.18, "interval_coverage_p10_p90": 0.8},
        ],
        "calibration": [
            {"risk_bin": "0-20%", "observed": 0.16, "predicted": 0.15},
            {"risk_bin": "20-40%", "observed": 0.31, "predicted": 0.34},
            {"risk_bin": "40-60%", "observed": 0.52, "predicted": 0.5},
            {"risk_bin": "60-80%", "observed": 0.7, "predicted": 0.72},
            {"risk_bin": "80-100%", "observed": 0.86, "predicted": 0.84},
        ],
        "drift_checks": [
            {"check": "arrival volume", "status": "watch", "note": "summer smoke season can shift arrivals outside winter-trained patterns"},
            {"check": "respiratory mix", "status": "stable", "note": "synthetic off-season levels within historical range"},
            {"check": "boarding relationship", "status": "watch", "note": "most sensitive to bed-board assumptions"},
        ],
        "limitations": [
            "Synthetic validation demonstrates product behavior only.",
            "Real deployment needs calibrated holdout validation using governed internal data.",
            "Scenario effects are directional and should not be treated as clinical recommendations.",
        ],
    }


def _scenario_catalog() -> dict[str, Any]:
    groups = [
        ("External Demand Shocks", [
            ("rsvSurge", "RSV surge intensity", 0, 100, "Increases pediatric respiratory arrivals and cohorting pressure."),
            ("influenzaSurge", "Influenza surge intensity", 0, 100, "Increases infectious/respiratory arrivals and admission-likely cases."),
            ("covidWave", "COVID wave intensity", 0, 100, "Raises respiratory isolation and diagnostics demand."),
            ("measlesCluster", "Measles exposure cluster", 0, 100, "Adds isolation and public-health-sensitive throughput friction."),
            ("schoolReopening", "School reopening effect", 0, 100, "Increases infectious, injury, and evening arrival patterns."),
            ("longWeekend", "Long weekend effect", 0, 100, "Shifts arrival timing and discharge/bed availability."),
            ("publicEvent", "Large public event", 0, 100, "Raises injury and access timing pressure."),
            ("smokeAqhi", "Smoke/AQHI deterioration", 0, 100, "Raises asthma/respiratory sensitivity and uncertainty."),
            ("heatWave", "Heat wave", 0, 100, "Adds dehydration and outdoor activity stress."),
            ("coldSnowstorm", "Extreme cold/snowstorm", 0, 100, "Adds access friction and acuity timing changes."),
            ("travelDisruption", "Travel/access disruption", 0, 100, "Clusters arrivals and interfacility movement delays."),
            ("catchmentShift", "Population/catchment demand shift", 0, 100, "Sustained demand increase across all arrival streams."),
        ]),
        ("Case-Mix and Acuity Shocks", [
            ("ctas12Increase", "CTAS 1-2 increase", 0, 100, "Raises resuscitation, physician, diagnostics, and admission pressure."),
            ("respiratoryCohorting", "Respiratory cohorting demand", 0, 100, "Consumes isolation and respiratory cohort space."),
            ("mentalHealthIncrease", "Mental health presentation increase", 0, 100, "Lengthens consult and disposition pathways."),
            ("traumaIncrease", "Trauma/injury increase", 0, 100, "Raises imaging, procedure, and critical-care pressure."),
            ("giOutbreak", "Dehydration/GI outbreak", 0, 100, "Raises arrivals and treatment-room dwell time."),
            ("oncologyPressure", "Oncology/immunocompromised pathway pressure", 0, 100, "Raises admission-likely and isolation-sensitive flows."),
            ("diagnosticHeavyMix", "Diagnostic-heavy case mix increase", 0, 100, "Raises diagnostic queue and LOS."),
        ]),
        ("ED Resource Levers", [
            ("triageNurseChange", "Triage nurse capacity change", -40, 60, "Changes triage service capacity."),
            ("physicianCoverageChange", "Physician coverage change", -40, 60, "Changes initial assessment throughput."),
            ("edNurseStaffingChange", "ED nurse staffing change", -40, 60, "Changes room turnover and treatment throughput."),
            ("roomAvailabilityChange", "Room availability change", -40, 60, "Changes pull from waiting room."),
            ("resusOccupancy", "Resuscitation space occupancy", 0, 100, "Consumes critical care spaces."),
            ("rapidAssessmentCapacity", "Rapid assessment zone capacity", 0, 100, "Improves initial assessment and low/moderate-acuity streaming."),
            ("fastTrackCapacity", "Fast-track capacity", 0, 100, "Shortens CTAS 4/5 waits and discharged LOS."),
            ("respiratoryPathwayCapacity", "Respiratory cohort pathway capacity", 0, 100, "Improves respiratory cohort throughput."),
            ("diagnosticTurnaround", "Diagnostics turnaround improvement", 0, 60, "Reduces diagnostic delay."),
            ("consultTurnaround", "Consult turnaround improvement", 0, 60, "Reduces consult delay and disposition waits."),
            ("mentalHealthSupport", "Social work/mental health support availability", 0, 100, "Reduces mental-health consult and disposition friction."),
            ("emsOffloadImprovement", "EMS offload process improvement", 0, 60, "Improves ambulance handoff and front-door smoothing."),
        ]),
        ("Inpatient and System Levers", [
            ("dischargeAcceleration", "Discharge acceleration", 0, 60, "Brings inpatient bed availability forward."),
            ("staffedBedAvailability", "Inpatient staffed-bed availability", -30, 60, "Changes receiving capacity."),
            ("medicineBedRelease", "Pediatric medicine bed release", 0, 60, "Targets highest-volume receiving service."),
            ("picuCapacity", "PICU receiving capacity", -30, 60, "Changes critical-care admission constraint."),
            ("surgeryCapacity", "Surgery receiving capacity", -30, 60, "Changes surgical boarding risk."),
            ("oncologyCapacity", "Oncology receiving capacity", -30, 60, "Changes specialty admission constraint."),
            ("mentalHealthCapacity", "Mental health receiving capacity", -30, 60, "Changes mental-health disposition constraint."),
            ("bedCleaningTurnaround", "Bed-cleaning turnaround", 0, 60, "Improves bed readiness timing."),
            ("transferOutThroughput", "Transfer-out throughput", 0, 60, "Relieves ED/inpatient congestion where transfer is appropriate."),
            ("transferInPressure", "Transfer-in pressure", 0, 100, "Raises tertiary referral and bed pressure."),
            ("isolationSeverity", "Isolation constraint severity", 0, 100, "Reduces flexible bed and room matching."),
        ]),
        ("Operational Workflow Options", [
            ("respiratorySurgePathway", "Activate respiratory surge pathway", 0, 1, "Switch; improves respiratory cohort throughput."),
            ("extendFastTrack", "Extend fast-track hours", 0, 1, "Switch; improves evening low-acuity flow."),
            ("rapidAssessmentProvider", "Add rapid assessment provider", 0, 1, "Switch; improves initial assessment."),
            ("pullToFull", "Pull-to-full rooming", 0, 1, "Switch; pulls waiting patients into rooms if nursing capacity supports it."),
            ("physicianInTriage", "Physician-in-triage style model", 0, 1, "Switch; reduces front-door physician wait for selected patients."),
            ("earlyBedHuddle", "Early inpatient bed huddle", 0, 1, "Switch; improves bed assignment timing."),
            ("dischargeBeforeNoon", "Discharge-before-noon improvement", 0, 1, "Switch; brings bed capacity forward."),
            ("consultantResponseTarget", "Consultant response target", 0, 1, "Switch; improves consult turnaround."),
            ("diagnosticPrioritization", "Diagnostic prioritization for admission-likely patients", 0, 1, "Switch; reduces admission decision delay."),
            ("temporaryFlexSpace", "Temporary flex space", 0, 1, "Switch; increases short-term rooming capacity with staffing caveat."),
        ]),
    ]
    controls = []
    for group, rows in groups:
        for control_id, label, minimum, maximum, mechanism in rows:
            controls.append(
                {
                    "id": control_id,
                    "label": label,
                    "group": group,
                    "min": minimum,
                    "max": maximum,
                    "default": 0,
                    "mechanism": mechanism,
                    "uncertainty_effect": "widens uncertainty under severe shocks" if maximum > 1 else "modest uncertainty change",
                }
            )
    return {"groups": [{"name": group, "control_count": len(rows)} for group, rows in groups], "controls": controls}


def _scenario_coefficients() -> dict[str, Any]:
    return {
        "normalization": "percentage controls are interpreted as control value / 100; binary options are 0 or 1",
        "metric_order": ["arrivals", "respiratory", "ctas12", "physicianWait", "dischargedLos", "admittedLos", "boarding", "lwbs", "roomUtilization", "physicianUtilization", "inpatientUtilization"],
        "controls": {
            "rsvSurge": {"demand": 0.16, "respiratory": 0.42, "wait": 0.12, "boarding": 0.07, "uncertainty": 0.1},
            "influenzaSurge": {"demand": 0.12, "respiratory": 0.28, "wait": 0.09, "boarding": 0.05, "uncertainty": 0.08},
            "covidWave": {"demand": 0.09, "respiratory": 0.22, "wait": 0.08, "boarding": 0.06, "uncertainty": 0.09},
            "measlesCluster": {"demand": 0.04, "respiratory": 0.08, "wait": 0.06, "boarding": 0.05, "isolation": 0.2, "uncertainty": 0.12},
            "schoolReopening": {"demand": 0.09, "respiratory": 0.08, "wait": 0.05, "boarding": 0.02, "uncertainty": 0.04},
            "longWeekend": {"demand": 0.06, "wait": 0.04, "boarding": 0.06, "uncertainty": 0.04},
            "publicEvent": {"demand": 0.05, "ctas12": 0.03, "wait": 0.04, "uncertainty": 0.03},
            "smokeAqhi": {"demand": 0.07, "respiratory": 0.18, "wait": 0.07, "uncertainty": 0.12},
            "heatWave": {"demand": 0.05, "wait": 0.04, "uncertainty": 0.06},
            "coldSnowstorm": {"demand": -0.02, "ctas12": 0.04, "wait": 0.08, "boarding": 0.07, "uncertainty": 0.1},
            "travelDisruption": {"demand": -0.01, "wait": 0.07, "boarding": 0.08, "ems": 0.12, "uncertainty": 0.11},
            "catchmentShift": {"demand": 0.14, "wait": 0.09, "boarding": 0.07, "uncertainty": 0.07},
            "ctas12Increase": {"ctas12": 0.34, "wait": 0.11, "boarding": 0.08, "los": 0.07, "uncertainty": 0.06},
            "respiratoryCohorting": {"respiratory": 0.22, "wait": 0.08, "boarding": 0.05, "isolation": 0.21, "uncertainty": 0.08},
            "mentalHealthIncrease": {"wait": 0.05, "boarding": 0.09, "los": 0.12, "uncertainty": 0.07},
            "traumaIncrease": {"ctas12": 0.12, "wait": 0.07, "los": 0.06, "boarding": 0.04, "uncertainty": 0.05},
            "giOutbreak": {"demand": 0.08, "wait": 0.06, "los": 0.04, "uncertainty": 0.04},
            "oncologyPressure": {"ctas12": 0.05, "wait": 0.06, "boarding": 0.12, "los": 0.09, "uncertainty": 0.08},
            "diagnosticHeavyMix": {"wait": 0.06, "los": 0.12, "uncertainty": 0.07},
            "triageNurseChange": {"wait": -0.1, "frontDoor": -0.22, "uncertainty": -0.02},
            "physicianCoverageChange": {"wait": -0.28, "lwbs": -0.12, "physicianUtilization": -0.18, "uncertainty": -0.03},
            "edNurseStaffingChange": {"wait": -0.12, "los": -0.09, "roomUtilization": -0.08, "uncertainty": -0.02},
            "roomAvailabilityChange": {"wait": -0.18, "roomUtilization": -0.16, "lwbs": -0.07, "uncertainty": -0.01},
            "resusOccupancy": {"ctas12": 0.08, "wait": 0.11, "boarding": 0.08, "uncertainty": 0.07},
            "rapidAssessmentCapacity": {"wait": -0.2, "lwbs": -0.09, "los": -0.04, "uncertainty": -0.02},
            "fastTrackCapacity": {"wait": -0.12, "lwbs": -0.12, "los": -0.08, "uncertainty": -0.02},
            "respiratoryPathwayCapacity": {"respiratory": -0.04, "wait": -0.08, "los": -0.06, "uncertainty": -0.02},
            "diagnosticTurnaround": {"los": -0.14, "wait": -0.03, "boarding": -0.02, "uncertainty": -0.02},
            "consultTurnaround": {"los": -0.09, "boarding": -0.07, "uncertainty": -0.02},
            "mentalHealthSupport": {"los": -0.08, "boarding": -0.05, "uncertainty": -0.02},
            "emsOffloadImprovement": {"wait": -0.04, "ems": -0.22, "uncertainty": -0.01},
            "dischargeAcceleration": {"boarding": -0.24, "inpatientUtilization": -0.12, "los": -0.05, "uncertainty": -0.03},
            "staffedBedAvailability": {"boarding": -0.26, "inpatientUtilization": -0.2, "los": -0.08, "uncertainty": -0.03},
            "medicineBedRelease": {"boarding": -0.18, "inpatientUtilization": -0.11, "los": -0.05, "uncertainty": -0.02},
            "picuCapacity": {"boarding": -0.08, "ctas12": -0.04, "uncertainty": -0.01},
            "surgeryCapacity": {"boarding": -0.08, "los": -0.03, "uncertainty": -0.01},
            "oncologyCapacity": {"boarding": -0.07, "los": -0.03, "uncertainty": -0.01},
            "mentalHealthCapacity": {"boarding": -0.08, "los": -0.04, "uncertainty": -0.01},
            "bedCleaningTurnaround": {"boarding": -0.12, "inpatientUtilization": -0.05, "uncertainty": -0.02},
            "transferOutThroughput": {"boarding": -0.06, "inpatientUtilization": -0.05, "uncertainty": -0.01},
            "transferInPressure": {"demand": 0.04, "boarding": 0.13, "uncertainty": 0.06},
            "isolationSeverity": {"wait": 0.07, "boarding": 0.1, "isolation": 0.22, "uncertainty": 0.08},
            "respiratorySurgePathway": {"respiratory": -0.04, "wait": -0.07, "los": -0.05, "uncertainty": -0.02},
            "extendFastTrack": {"wait": -0.06, "lwbs": -0.05, "los": -0.03, "uncertainty": -0.01},
            "rapidAssessmentProvider": {"wait": -0.09, "lwbs": -0.04, "uncertainty": -0.02},
            "pullToFull": {"wait": -0.07, "roomUtilization": 0.04, "uncertainty": 0.01},
            "physicianInTriage": {"wait": -0.08, "lwbs": -0.05, "uncertainty": -0.02},
            "earlyBedHuddle": {"boarding": -0.08, "inpatientUtilization": -0.03, "uncertainty": -0.01},
            "dischargeBeforeNoon": {"boarding": -0.08, "inpatientUtilization": -0.05, "uncertainty": -0.01},
            "consultantResponseTarget": {"boarding": -0.05, "los": -0.04, "uncertainty": -0.01},
            "diagnosticPrioritization": {"los": -0.06, "boarding": -0.03, "uncertainty": -0.01},
            "temporaryFlexSpace": {"wait": -0.06, "roomUtilization": -0.04, "uncertainty": 0.02},
        },
        "nonlinear_rules": [
            "resource improvements are dampened when inpatient receiving capacity remains binding",
            "severe external shocks widen uncertainty more than moderate shocks",
            "LWBS hazard responds more strongly after physician wait exceeds 180 minutes",
            "boarding improvements can reveal physician assessment or rooming as the next bottleneck",
        ],
    }


def _scenario_presets() -> list[dict[str, Any]]:
    return [
        {"id": "winter_respiratory", "name": "Typical winter respiratory surge", "description": "Moderate RSV/influenza rise with school-week pressure.", "controls": {"rsvSurge": 55, "influenzaSurge": 35, "schoolReopening": 25, "respiratoryCohorting": 45}},
        {"id": "severe_rsv", "name": "Severe RSV week", "description": "High RSV, respiratory cohorting, and PICU-sensitive demand.", "controls": {"rsvSurge": 85, "respiratoryCohorting": 75, "ctas12Increase": 25, "picuCapacity": -10}},
        {"id": "smoke_respiratory", "name": "Smoke plus respiratory sensitivity", "description": "AQHI deterioration layered onto respiratory-vulnerable demand.", "controls": {"smokeAqhi": 80, "respiratoryCohorting": 45, "diagnosticHeavyMix": 25}},
        {"id": "snowstorm_access", "name": "Snowstorm access disruption", "description": "Access friction and lumpy arrivals with offload sensitivity.", "controls": {"coldSnowstorm": 75, "travelDisruption": 70, "emsOffloadImprovement": 0}},
        {"id": "boarding_heavy", "name": "Boarding-heavy day", "description": "Inpatient receiving pressure dominates the ED operating picture.", "controls": {"staffedBedAvailability": -20, "transferInPressure": 55, "isolationSeverity": 45}},
        {"id": "staffing_shortfall", "name": "Staffing shortfall", "description": "ED nursing, physician, and triage capacity under baseline.", "controls": {"triageNurseChange": -20, "physicianCoverageChange": -15, "edNurseStaffingChange": -18, "roomAvailabilityChange": -10}},
        {"id": "discharge_acceleration", "name": "Discharge acceleration", "description": "Bed release, cleaning, and early huddle pull capacity forward.", "controls": {"dischargeAcceleration": 45, "bedCleaningTurnaround": 35, "earlyBedHuddle": 1, "dischargeBeforeNoon": 1}},
        {"id": "fast_track_expansion", "name": "Fast-track expansion", "description": "Low-acuity streaming and extended fast-track hours.", "controls": {"fastTrackCapacity": 50, "extendFastTrack": 1, "roomAvailabilityChange": 10}},
        {"id": "rapid_assessment", "name": "Rapid assessment intervention", "description": "Front-door physician/rapid-assessment capacity to reduce initial waits.", "controls": {"rapidAssessmentCapacity": 55, "rapidAssessmentProvider": 1, "physicianInTriage": 1}},
        {"id": "combined_high_pressure", "name": "Combined high-pressure week", "description": "Respiratory, access, staffing, and boarding pressure at once.", "controls": {"rsvSurge": 70, "influenzaSurge": 45, "smokeAqhi": 35, "travelDisruption": 40, "ctas12Increase": 30, "physicianCoverageChange": -10, "staffedBedAvailability": -15, "isolationSeverity": 55}},
    ]


def _scenario_results_grid(
    baseline: dict[str, Any],
    current_state: dict[str, Any],
    unit_capacity: dict[str, Any],
    coefficients: dict[str, Any],
    presets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grid = []
    for preset in presets:
        summary = _apply_controls_to_summary(baseline["baseline_summary"], preset["controls"], coefficients["controls"])
        grid.append(
            {
                "preset_id": preset["id"],
                "preset_name": preset["name"],
                "baseline": baseline["baseline_summary"],
                "scenario": summary,
                "delta": _delta(baseline["baseline_summary"], summary),
                "bottleneck_shift": _bottleneck_shift(summary),
                "highest_yield_lever": _highest_yield_lever(preset["controls"]),
                "watch_points": _watch_points(summary),
            }
        )
    return grid


def _apply_controls_to_summary(base: dict[str, Any], controls: dict[str, float], coefficients: dict[str, dict[str, float]]) -> dict[str, Any]:
    effects = {"demand": 0.0, "respiratory": 0.0, "ctas12": 0.0, "wait": 0.0, "los": 0.0, "boarding": 0.0, "lwbs": 0.0, "roomUtilization": 0.0, "physicianUtilization": 0.0, "inpatientUtilization": 0.0, "uncertainty": 0.0}
    for key, raw_value in controls.items():
        control_coeffs = coefficients.get(key, {})
        norm = raw_value if abs(raw_value) <= 1 and key in {"respiratorySurgePathway", "extendFastTrack", "rapidAssessmentProvider", "pullToFull", "physicianInTriage", "earlyBedHuddle", "dischargeBeforeNoon", "consultantResponseTarget", "diagnosticPrioritization", "temporaryFlexSpace"} else raw_value / 100
        for effect, coeff in control_coeffs.items():
            if effect in effects:
                effects[effect] += coeff * norm
    stress = max(0.0, effects["demand"] + effects["ctas12"] + effects["boarding"])
    wait_multiplier = max(0.55, 1 + effects["wait"] + effects["demand"] * 0.85 + effects["ctas12"] * 0.55 + max(0, effects["boarding"]) * 0.38)
    boarding_multiplier = max(0.45, 1 + effects["boarding"] + effects["demand"] * 0.25 + effects["ctas12"] * 0.2)
    arrivals = base["arrivals_72h"] * max(0.75, 1 + effects["demand"])
    wait = base["median_physician_wait_mins"] * wait_multiplier
    boarding = base["boarding_hours_72h"] * boarding_multiplier
    lwbs = np.clip(base["lwbs_risk_peak"] * (1 + effects["lwbs"] + max(0, wait - 180) / 500), 0.005, 0.18)
    return {
        "arrivals_72h": round(float(arrivals), 1),
        "median_physician_wait_mins": round(float(wait), 1),
        "p90_physician_wait_mins": round(float(base["p90_physician_wait_mins"] * wait_multiplier * (1 + max(0, effects["uncertainty"]) * 0.6)), 1),
        "boarding_hours_72h": round(float(boarding), 1),
        "lwbs_risk_peak": round(float(lwbs), 3),
        "primary_bottleneck": _bottleneck_shift({"wait_effect": effects["wait"], "boarding_effect": effects["boarding"], "demand_effect": effects["demand"]}),
        "next_bottleneck": "Physician initial assessment" if effects["boarding"] < -0.08 else "Rooming and inpatient receiving",
        "uncertainty_width": round(float(1 + max(0, effects["uncertainty"]) + stress * 0.35), 2),
        "effect_vector": {key: round(float(value), 3) for key, value in effects.items()},
    }


def _delta(base: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "arrivals_72h": round(scenario["arrivals_72h"] - base["arrivals_72h"], 1),
        "median_physician_wait_mins": round(scenario["median_physician_wait_mins"] - base["median_physician_wait_mins"], 1),
        "p90_physician_wait_mins": round(scenario["p90_physician_wait_mins"] - base["p90_physician_wait_mins"], 1),
        "boarding_hours_72h": round(scenario["boarding_hours_72h"] - base["boarding_hours_72h"], 1),
        "lwbs_risk_peak": round(scenario["lwbs_risk_peak"] - base["lwbs_risk_peak"], 3),
    }


def _bottleneck_shift(summary: dict[str, Any]) -> str:
    if "boarding_effect" in summary:
        if summary["boarding_effect"] > 0.06:
            return "Inpatient receiving capacity"
        if summary["wait_effect"] < -0.08:
            return "Boarding remains downstream constraint"
        if summary["wait_effect"] > 0.05:
            return "Physician initial assessment"
        return "Rooming and diagnostics"
    if summary.get("boarding_hours_72h", 0) > 1100:
        return "Inpatient receiving capacity"
    if summary.get("median_physician_wait_mins", 0) > 210:
        return "Physician initial assessment"
    return "Rooming and diagnostics"


def _highest_yield_lever(controls: dict[str, float]) -> str:
    if any(key in controls for key in ["dischargeAcceleration", "staffedBedAvailability", "bedCleaningTurnaround"]):
        return "Bed release and discharge timing"
    if any(key in controls for key in ["rapidAssessmentCapacity", "rapidAssessmentProvider", "physicianInTriage"]):
        return "Rapid assessment / initial physician assessment"
    if any(key in controls for key in ["fastTrackCapacity", "extendFastTrack"]):
        return "Fast-track streaming"
    if any(key in controls for key in ["respiratorySurgePathway", "respiratoryPathwayCapacity"]):
        return "Respiratory cohort pathway"
    return "Integrated capacity huddle"


def _watch_points(summary: dict[str, Any]) -> list[str]:
    points = ["arrival shape after school/evening hours", "CTAS 1-2 and respiratory cohort mix"]
    if summary.get("boarding_hours_72h", 0) > 1000:
        points.append("decision-to-admit boarders and inpatient bed readiness")
    if summary.get("median_physician_wait_mins", 0) > 180:
        points.append("physician initial assessment queue and LWBS risk")
    points.append("whether the intervention moves the bottleneck downstream rather than removing it")
    return points


def _huddle_briefs(grid: list[dict[str, Any]]) -> dict[str, Any]:
    scenario_briefs = {}
    for row in grid:
        delta = row["delta"]
        scenario_briefs[row["preset_id"]] = [
            f"{row['preset_name']}: physician wait changes by {delta['median_physician_wait_mins']:+.0f} minutes versus baseline.",
            f"Boarding changes by {delta['boarding_hours_72h']:+.0f} hours over 72 hours; bottleneck shifts toward {row['bottleneck_shift']}.",
            f"Highest-yield lever to test first: {row['highest_yield_lever']}.",
            "Watch the next 4-12 hours for queue growth, room turnover, and inpatient bed timing.",
            "This read can break if real-time acuity, staffing, diagnostics, or bed-board state differs from the synthetic assumptions.",
        ]
    return {
        "baseline": [
            "Stollery synthetic state is moderate-high pressure with boarding as the primary constraint.",
            "Public pressure is not a live operations feed; it is context for demand sensitivity.",
            "The next likely bottleneck is physician initial assessment if evening arrivals rise.",
            "Highest-yield watch area is inpatient receiving capacity and discharge timing.",
            "Use scenario comparisons as directional huddle support, not automated decision-making.",
        ],
        "scenarios": scenario_briefs,
    }


def _ui_copy() -> dict[str, Any]:
    return {
        "hero": {
            "title": "Reimagining Alberta ED Flow Intelligence",
            "subtitle": "A Stollery-focused public showcase of open-data pressure signals, synthetic operating state, predictive modelling, and scenario-based flow intelligence.",
            "caveat": "Public + synthetic demonstration. No real patient data.",
        },
        "sections": [
            {"id": "open-data", "label": "Open Data Context", "nav": "Open Data"},
            {"id": "synthetic-state", "label": "Synthetic Stollery ED Operating Reality", "nav": "Synthetic ED State"},
            {"id": "predictive-intelligence", "label": "Blended Predictive Intelligence", "nav": "Predictive Intelligence"},
            {"id": "scenario-studio", "label": "Scenario & What-If Studio", "nav": "Scenario Studio"},
        ],
        "tone": "confident, honest, executive-friendly, pediatric, operationally useful",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Stollery public showcase artifacts.")
    parser.add_argument("--out", required=True, help="Output directory for JSON artifacts.")
    parser.add_argument("--seed", type=int, default=20260601, help="Deterministic export seed.")
    parser.add_argument("--mode", default="public_demo", help="Compatibility label for public demo mode.")
    args = parser.parse_args()
    written = export_stollery_public_showcase_artifacts(args.out, seed=args.seed, mode=args.mode)
    print(f"Exported {len(written)} Stollery public showcase artifacts to {Path(args.out).resolve()}")


if __name__ == "__main__":
    main()
