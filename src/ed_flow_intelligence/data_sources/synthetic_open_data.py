"""Synthetic public/open-data cache for the external v2 prototype."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


OPEN_DATA_DIR = Path("data/open")
SYNTHETIC_OPEN_NOW = datetime(2026, 5, 31, 9, 0, 0)


FACILITY_REFERENCE = [
    ("Stollery Children's Hospital", "Edmonton", "Edmonton", 53.536, -113.500, "Pediatric Academic", True),
    ("Alberta Children's Hospital", "Calgary", "Calgary", 51.074, -114.148, "Pediatric Academic", True),
    ("Royal Alexandra Hospital", "Edmonton", "Edmonton", 53.558, -113.497, "Urban Tertiary", False),
    ("Foothills Medical Centre", "Calgary", "Calgary", 51.065, -114.133, "Urban Tertiary", False),
    ("Red Deer Regional Hospital Centre", "Central", "Red Deer", 52.269, -113.811, "Regional", False),
    ("Northeast Community Health Centre", "Edmonton", "Edmonton", 53.596, -113.407, "Urban Community", False),
    ("South Calgary Ambulatory Care Centre", "Calgary", "Calgary", 50.900, -114.063, "Ambulatory", False),
]


def generate_facility_reference() -> pd.DataFrame:
    """Return public site-reference features with no patient data."""

    return pd.DataFrame(
        FACILITY_REFERENCE,
        columns=["facility", "zone", "city", "latitude", "longitude", "peer_group", "pediatric_site"],
    )


def generate_public_wait_times(seed: int = 120) -> pd.DataFrame:
    """Generate AHS-posted-wait-time-shaped synthetic public data."""

    rng = np.random.default_rng(seed)
    facilities = generate_facility_reference()
    rows: list[dict[str, object]] = []
    for _, facility in facilities.iterrows():
        base = 95 if facility["pediatric_site"] else 120
        if facility["peer_group"] == "Ambulatory":
            base = 70
        for hour_back in range(48, -1, -1):
            timestamp = SYNTHETIC_OPEN_NOW - timedelta(hours=hour_back)
            diurnal = 24 * np.sin((timestamp.hour - 9) / 24 * 2 * np.pi)
            noise = rng.normal(0, 16)
            wait = int(np.clip(base + diurnal + noise, 12, 260))
            rows.append(
                {
                    "facility": facility["facility"],
                    "zone": facility["zone"],
                    "city": facility["city"],
                    "posted_timestamp": timestamp,
                    "estimated_wait_mins": wait,
                    "site_open": True,
                    "public_message": "Synthetic fallback shaped like public estimated ED wait times.",
                    "source_category": "HYBRID_OPEN_SYNTHETIC",
                    "official_source": "AHS estimated ED wait times",
                }
            )
    return pd.DataFrame(rows)


def generate_historical_public_ed_metrics(seed: int = 121) -> pd.DataFrame:
    """Generate public aggregate ED-performance metrics for validation context."""

    rng = np.random.default_rng(seed)
    facilities = generate_facility_reference()
    rows = []
    for _, facility in facilities.iterrows():
        for week in range(16):
            start = SYNTHETIC_OPEN_NOW.date() - timedelta(days=7 * week)
            visits = int(rng.integers(450, 1400) * (0.65 if facility["pediatric_site"] else 1.0))
            rows.append(
                {
                    "facility": facility["facility"],
                    "zone": facility["zone"],
                    "week_start": pd.Timestamp(start),
                    "public_visits": visits,
                    "discharged_within_4h_pct": float(np.clip(rng.normal(0.38, 0.09), 0.08, 0.82)),
                    "admitted_within_8h_pct": float(np.clip(rng.normal(0.41, 0.1), 0.05, 0.85)),
                    "source_category": "HYBRID_OPEN_SYNTHETIC",
                }
            )
    return pd.DataFrame(rows)


def generate_respiratory_surveillance(seed: int = 122) -> pd.DataFrame:
    """Generate public respiratory surveillance context by zone and week."""

    rng = np.random.default_rng(seed)
    zones = ["Edmonton", "Calgary", "Central", "North", "South"]
    viruses = ["RSV", "Influenza", "COVID-19", "Other respiratory"]
    rows = []
    for zone in zones:
        zone_bias = {"Edmonton": 0.9, "Calgary": 1.0, "Central": 0.75, "North": 0.65, "South": 0.7}[zone]
        for week in range(18):
            week_start = pd.Timestamp(SYNTHETIC_OPEN_NOW.date() - timedelta(days=7 * week))
            seasonal = 1.0 + 0.45 * np.sin((week + 4) / 18 * 2 * np.pi)
            for virus in viruses:
                multiplier = {"RSV": 1.25, "Influenza": 1.05, "COVID-19": 0.8, "Other respiratory": 0.65}[virus]
                positivity = float(np.clip(rng.normal(0.11 * multiplier * seasonal * zone_bias, 0.035), 0.01, 0.34))
                rows.append(
                    {
                        "zone": zone,
                        "week_start": week_start,
                        "pathogen": virus,
                        "test_positivity": positivity,
                        "new_hospital_admissions": int(np.clip(rng.normal(45 * multiplier * seasonal * zone_bias, 14), 0, 170)),
                        "pediatric_pressure_index": float(np.clip(positivity * 2.7 + rng.normal(0.05, 0.04), 0, 1)),
                        "school_absenteeism_proxy": float(np.clip(positivity * 1.8 + rng.normal(0.08, 0.04), 0, 1)),
                        "source_category": "HYBRID_OPEN_SYNTHETIC",
                    }
                )
    return pd.DataFrame(rows)


def generate_environmental_stress(seed: int = 123) -> pd.DataFrame:
    """Generate synthetic weather, smoke, heat, wildfire, and AQHI features."""

    rng = np.random.default_rng(seed)
    facilities = generate_facility_reference()
    rows = []
    for _, facility in facilities.iterrows():
        smoke_bias = 0.18 if facility["zone"] in {"Edmonton", "Central"} else 0.12
        for hour in range(0, 96):
            ts = SYNTHETIC_OPEN_NOW + timedelta(hours=hour)
            temp = 18 + 7 * np.sin((ts.hour - 11) / 24 * 2 * np.pi) + rng.normal(0, 2.2)
            humidex = temp + max(0, rng.normal(3.5, 2.0))
            smoke = float(np.clip(rng.beta(1.3, 5.0) + smoke_bias, 0, 1))
            aqhi = int(np.clip(round(2 + smoke * 7 + rng.normal(0, 1.2)), 1, 10))
            heat_alert = bool(humidex >= 29 and rng.random() < 0.35)
            rows.append(
                {
                    "facility": facility["facility"],
                    "zone": facility["zone"],
                    "city": facility["city"],
                    "timestamp": ts,
                    "temperature_c": round(float(temp), 1),
                    "humidex": round(float(humidex), 1),
                    "aqhi": aqhi,
                    "wildfire_smoke_risk": smoke,
                    "weather_alert_count": int(rng.poisson(0.22 + 0.6 * heat_alert + 0.45 * (aqhi >= 7))),
                    "heat_alert": heat_alert,
                    "environmental_stress_index": float(np.clip((aqhi / 10) * 0.45 + smoke * 0.35 + heat_alert * 0.2, 0, 1)),
                    "source_category": "HYBRID_OPEN_SYNTHETIC",
                }
            )
    return pd.DataFrame(rows)


def generate_travel_friction(seed: int = 124) -> pd.DataFrame:
    """Generate road, traffic, transit, and event access-friction features."""

    rng = np.random.default_rng(seed)
    facilities = generate_facility_reference()
    rows = []
    for _, facility in facilities.iterrows():
        urban = facility["city"] in {"Edmonton", "Calgary"}
        for hour in range(0, 96):
            ts = SYNTHETIC_OPEN_NOW + timedelta(hours=hour)
            rush = ts.hour in {7, 8, 15, 16, 17}
            incidents = int(rng.poisson((1.2 if urban else 0.45) + (1.0 if rush else 0.0)))
            closures = int(rng.poisson(0.45 if urban else 0.18))
            transit = float(np.clip(rng.beta(1.4, 5.5) + (0.12 if rush and urban else 0), 0, 1))
            event = float(np.clip(rng.beta(1.2, 7.0) + (0.22 if ts.weekday() >= 5 and urban else 0), 0, 1))
            friction = float(np.clip(0.12 * incidents + 0.18 * closures + 0.28 * transit + 0.22 * event, 0, 1))
            rows.append(
                {
                    "facility": facility["facility"],
                    "zone": facility["zone"],
                    "city": facility["city"],
                    "timestamp": ts,
                    "road_incidents": incidents,
                    "road_closures": closures,
                    "transit_disruption_index": transit,
                    "major_event_index": event,
                    "travel_friction_index": friction,
                    "source_category": "HYBRID_OPEN_SYNTHETIC",
                }
            )
    return pd.DataFrame(rows)


def generate_calendar_context() -> pd.DataFrame:
    """Generate public calendar features for demand modelling."""

    holidays = [
        ("New Year's Day", "2026-01-01"),
        ("Alberta Family Day", "2026-02-16"),
        ("Good Friday", "2026-04-03"),
        ("Victoria Day", "2026-05-18"),
        ("Canada Day", "2026-07-01"),
        ("Labour Day", "2026-09-07"),
        ("Thanksgiving Day", "2026-10-12"),
        ("Remembrance Day", "2026-11-11"),
        ("Christmas Day", "2026-12-25"),
    ]
    rows = [
        {
            "date": pd.Timestamp(date),
            "calendar_label": name,
            "calendar_type": "Alberta general holiday",
            "school_in_session": False,
            "source_category": "OPEN_DATA",
        }
        for name, date in holidays
    ]
    rows.extend(
        {
            "date": pd.Timestamp(SYNTHETIC_OPEN_NOW.date() + timedelta(days=day)),
            "calendar_label": "Regular school weekday" if day % 7 not in {5, 6} else "Weekend",
            "calendar_type": "Synthetic school calendar feature",
            "school_in_session": day % 7 not in {5, 6},
            "source_category": "HYBRID_OPEN_SYNTHETIC",
        }
        for day in range(60)
    )
    return pd.DataFrame(rows)


def generate_population_context(seed: int = 125) -> pd.DataFrame:
    """Generate non-identifying public catchment context by site."""

    rng = np.random.default_rng(seed)
    facilities = generate_facility_reference()
    rows = []
    for _, facility in facilities.iterrows():
        rows.append(
            {
                "facility": facility["facility"],
                "zone": facility["zone"],
                "city": facility["city"],
                "pediatric_catchment_population": int(rng.integers(85000, 260000) if facility["pediatric_site"] else rng.integers(25000, 120000)),
                "all_age_catchment_population": int(rng.integers(180000, 850000)),
                "rurality_access_index": float(np.clip(rng.beta(1.6, 4.0) + (0.18 if facility["zone"] == "Central" else 0), 0, 1)),
                "source_category": "HYBRID_OPEN_SYNTHETIC",
            }
        )
    return pd.DataFrame(rows)


PUBLIC_DATA_GENERATORS = {
    "facility_reference": generate_facility_reference,
    "public_wait_times": generate_public_wait_times,
    "historical_public_ed_metrics": generate_historical_public_ed_metrics,
    "respiratory_surveillance": generate_respiratory_surveillance,
    "environmental_stress": generate_environmental_stress,
    "travel_friction": generate_travel_friction,
    "calendar_context": generate_calendar_context,
    "population_context": generate_population_context,
}


def ensure_public_open_data(data_dir: Path = OPEN_DATA_DIR, force: bool = False) -> dict[str, Path]:
    """Write local public/open-data cache CSVs if they are missing."""

    data_dir.mkdir(parents=True, exist_ok=True)
    paths = {name: data_dir / f"{name}.csv" for name in PUBLIC_DATA_GENERATORS}
    if not force and all(path.exists() for path in paths.values()):
        return paths
    for name, generator in PUBLIC_DATA_GENERATORS.items():
        generator().to_csv(paths[name], index=False)
    return paths


def load_public_open_data(data_dir: Path = OPEN_DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load all public/open-data cache frames."""

    paths = ensure_public_open_data(data_dir)
    timestamp_cols = {
        "public_wait_times": ["posted_timestamp"],
        "historical_public_ed_metrics": ["week_start"],
        "respiratory_surveillance": ["week_start"],
        "environmental_stress": ["timestamp"],
        "travel_friction": ["timestamp"],
        "calendar_context": ["date"],
    }
    data: dict[str, pd.DataFrame] = {}
    for name, path in paths.items():
        frame = pd.read_csv(path)
        for column in timestamp_cols.get(name, []):
            if column in frame.columns:
                frame[column] = pd.to_datetime(frame[column], errors="coerce")
        data[name] = frame
    return data
