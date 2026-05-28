"""Discrete-event ED flow simulation with deterministic local fallback."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ed_flow.data_contracts import ScenarioConfig
from ed_flow.feature_engineering import estimate_baseline_parameters


try:
    import simpy as _simpy  # noqa: F401

    SIMPY_AVAILABLE = True
except Exception:
    SIMPY_AVAILABLE = False


@dataclass
class SimulationOutput:
    """Container for simulation output tables."""

    summary: pd.DataFrame
    patients: pd.DataFrame
    queue_lengths: pd.DataFrame
    bottlenecks: pd.DataFrame


def _sample_lognormal(rng: np.random.Generator, median: float, sigma: float, minimum: float, maximum: float) -> float:
    value = float(rng.lognormal(mean=np.log(max(median, 0.01)), sigma=sigma))
    return float(np.clip(value, minimum, maximum))


def _allocate_resource(available: np.ndarray, ready_time: float, duration: float) -> tuple[float, float, np.ndarray]:
    idx = int(np.argmin(available))
    start = max(float(available[idx]), ready_time)
    finish = start + duration
    available[idx] = finish
    return start, finish, available


def run_single_replication(
    baseline: dict[str, object],
    scenario: ScenarioConfig,
    replication: int,
) -> pd.DataFrame:
    """Run one reproducible stochastic replication."""

    rng = np.random.default_rng(scenario.random_seed + replication)
    rate = float(baseline.get("arrival_rate_per_hour", 2.0)) * scenario.arrival_surge_multiplier
    expected_n = max(int(rate * scenario.horizon_hours), 1)
    interarrivals = rng.exponential(1 / max(rate, 0.01), size=expected_n * 3)
    arrival_times = np.cumsum(interarrivals)
    arrival_times = arrival_times[arrival_times <= scenario.horizon_hours]
    if arrival_times.size == 0:
        arrival_times = np.array([0.1])

    triage_capacity = max(1, int(baseline.get("triage_capacity", 2)) + scenario.triage_capacity_delta)
    room_capacity = max(1, int(baseline.get("room_capacity", 18)) + scenario.rooming_capacity_delta)
    physician_capacity = max(1, int(baseline.get("physician_capacity", 5)) + scenario.physician_capacity_delta)
    triage_available = np.zeros(triage_capacity)
    room_available = np.zeros(room_capacity)
    physician_available = np.zeros(physician_capacity)

    triage_probs = baseline.get("arrival_by_triage", {"1": 0.02, "2": 0.14, "3": 0.43, "4": 0.29, "5": 0.12})
    triage_levels = sorted(int(k) for k in triage_probs)
    triage_weights = np.array([float(triage_probs[str(k)]) for k in triage_levels])
    triage_weights = triage_weights / triage_weights.sum()
    disposition_probs = baseline.get("disposition_probs", {"Admitted": 0.2, "Discharged": 0.65, "LWBS": 0.08, "Transferred": 0.04})
    disposition_labels = list(disposition_probs.keys())
    disposition_weights = np.array([float(v) for v in disposition_probs.values()])
    disposition_weights = disposition_weights / disposition_weights.sum()

    rows = []
    for patient_idx, arrival in enumerate(arrival_times):
        triage = int(rng.choice(triage_levels, p=triage_weights))
        registration_finish = arrival + _sample_lognormal(
            rng,
            float(baseline.get("registration_median_mins", 8)) / 60,
            0.35,
            1 / 60,
            1.0,
        )
        triage_duration = _sample_lognormal(
            rng,
            float(baseline.get("triage_service_median_mins", 10)) / 60,
            0.32,
            3 / 60,
            0.8,
        )
        triage_start, triage_finish, triage_available = _allocate_resource(
            triage_available, registration_finish, triage_duration
        )
        fast_track = bool(scenario.fast_track_enabled and triage in {4, 5})
        room_ready = triage_finish
        if fast_track:
            room_ready += _sample_lognormal(rng, 0.2, 0.45, 0.0, 2.0)
        room_duration = _sample_lognormal(
            rng,
            max(float(baseline.get("rooming_wait_median_hrs", 1.0)) * (0.55 if fast_track else 1.0), 0.05),
            0.55,
            0.0,
            8.0,
        )
        room_start, room_finish, room_available = _allocate_resource(room_available, room_ready, room_duration)
        physician_duration = _sample_lognormal(
            rng,
            max(float(baseline.get("physician_wait_median_hrs", 0.6)) * (0.75 if fast_track else 1.0), 0.05),
            0.5,
            0.0,
            6.0,
        )
        pia_start, pia_finish, physician_available = _allocate_resource(
            physician_available, room_finish, physician_duration
        )
        has_consult = rng.random() < float(baseline.get("consult_probability", 0.18))
        consult_delay = (
            _sample_lognormal(
                rng,
                float(baseline.get("consult_delay_median_hrs", 2.0)) * (1 - scenario.consult_turnaround_improvement),
                0.55,
                0.1,
                12,
            )
            if has_consult
            else 0.0
        )
        diagnostic_delay = _sample_lognormal(
            rng,
            1.1 * (1 - scenario.diagnostic_turnaround_improvement),
            0.45,
            0.1,
            8.0,
        )
        disposition = str(rng.choice(disposition_labels, p=disposition_weights))
        treatment_base = _sample_lognormal(rng, 1.8 if triage <= 3 else 1.05, 0.55, 0.2, 10)
        if disposition == "Discharged":
            treatment_base *= 1 - scenario.discharge_acceleration
        disposition_time = pia_finish + treatment_base + max(consult_delay, diagnostic_delay)
        boarding_hours = 0.0
        if disposition == "Admitted":
            boarding_hours = _sample_lognormal(
                rng,
                float(baseline.get("boarding_delay_median_hrs", 4.0))
                * (1 - scenario.boarding_reduction)
                * (1 - scenario.admission_bed_improvement),
                0.65,
                0.2,
                24,
            )
        ems_offload_delay = 0.0
        if rng.random() < 0.18:
            ems_offload_delay = _sample_lognormal(rng, 0.45 * (1 - scenario.ems_offload_improvement), 0.6, 0, 4)
        ed_departure = disposition_time + boarding_hours + ems_offload_delay
        wait_to_physician = max(pia_start - arrival, 0)
        lwbs_probability = float(np.clip(0.03 + 0.03 * max(wait_to_physician - 2.0, 0) + (0.03 if triage >= 4 else 0), 0, 0.75))
        if rng.random() < lwbs_probability and wait_to_physician > 1.0:
            disposition = "LWBS"
            ed_departure = triage_finish + _sample_lognormal(rng, 1.2, 0.7, 0.1, 8)
            boarding_hours = 0.0
        rows.append(
            {
                "replication": replication,
                "patient_id": patient_idx,
                "arrival_time_hr": arrival,
                "triage_level": triage,
                "triage_wait_hrs": max(triage_start - registration_finish, 0),
                "rooming_wait_hrs": max(room_start - triage_finish, 0),
                "wait_to_physician_hrs": wait_to_physician,
                "consult_delay_hrs": consult_delay,
                "diagnostic_delay_hrs": diagnostic_delay,
                "boarding_hours": boarding_hours,
                "ems_offload_delay_hrs": ems_offload_delay,
                "ed_los_hrs": max(ed_departure - arrival, 0),
                "disposition": disposition,
                "admitted_within_8_hours": bool(disposition == "Admitted" and ed_departure - arrival <= 8),
                "discharged_within_4_hours": bool(disposition == "Discharged" and ed_departure - arrival <= 4),
                "lwbs_risk": lwbs_probability,
                "fast_track": fast_track,
            }
        )
    return pd.DataFrame(rows)


def summarize_replications(patients: pd.DataFrame) -> pd.DataFrame:
    """Summarize patient-level simulation output by replication."""

    rows = []
    for rep, group in patients.groupby("replication"):
        admitted = group["disposition"].eq("Admitted")
        discharged = group["disposition"].eq("Discharged")
        rows.append(
            {
                "replication": rep,
                "visits": int(len(group)),
                "median_wait_hrs": float(group["wait_to_physician_hrs"].median()),
                "p90_wait_hrs": float(group["wait_to_physician_hrs"].quantile(0.9)),
                "median_ed_los_hrs": float(group["ed_los_hrs"].median()),
                "p90_ed_los_hrs": float(group["ed_los_hrs"].quantile(0.9)),
                "admitted_within_8_hours": float(group.loc[admitted, "admitted_within_8_hours"].mean()) if admitted.any() else np.nan,
                "discharged_within_4_hours": float(group.loc[discharged, "discharged_within_4_hours"].mean()) if discharged.any() else np.nan,
                "lwbs_risk": float(group["lwbs_risk"].mean()),
                "boarding_hours": float(group["boarding_hours"].sum()),
            }
        )
    return pd.DataFrame(rows)


def queue_lengths_over_time(patients: pd.DataFrame, horizon_hours: int) -> pd.DataFrame:
    """Approximate hourly queue pressure for charting."""

    rows = []
    for rep, group in patients.groupby("replication"):
        for hour in range(horizon_hours + 1):
            arrived = group["arrival_time_hr"] <= hour
            waiting = arrived & (group["arrival_time_hr"] + group["wait_to_physician_hrs"] > hour)
            boarding = arrived & (group["boarding_hours"] > 0) & (group["arrival_time_hr"] + group["ed_los_hrs"] > hour)
            rows.append(
                {
                    "replication": rep,
                    "hour": hour,
                    "waiting_for_physician": int(waiting.sum()),
                    "boarding": int(boarding.sum()),
                    "total_active_pressure": int(waiting.sum() + boarding.sum()),
                }
            )
    return pd.DataFrame(rows)


def bottleneck_shift_analysis(patients: pd.DataFrame) -> pd.DataFrame:
    """Identify which simulated stage contributes the most delay."""

    stage_cols = {
        "Rooming wait": "rooming_wait_hrs",
        "Physician initial assessment": "wait_to_physician_hrs",
        "Consult delay": "consult_delay_hrs",
        "Diagnostics": "diagnostic_delay_hrs",
        "Boarding": "boarding_hours",
        "EMS offload": "ems_offload_delay_hrs",
    }
    rows = []
    total = 0.0
    for label, column in stage_cols.items():
        value = float(patients[column].sum()) if column in patients else 0.0
        total += value
        rows.append({"bottleneck": label, "total_delay_hours": value})
    out = pd.DataFrame(rows)
    out["share_of_delay"] = out["total_delay_hours"] / max(total, 1e-9)
    return out.sort_values("total_delay_hours", ascending=False).reset_index(drop=True)


def summarize_with_uncertainty(replication_summary: pd.DataFrame) -> pd.DataFrame:
    """Convert replication summaries into mean and 80% interval table."""

    metrics = [
        "median_wait_hrs",
        "p90_wait_hrs",
        "median_ed_los_hrs",
        "p90_ed_los_hrs",
        "admitted_within_8_hours",
        "discharged_within_4_hours",
        "lwbs_risk",
        "boarding_hours",
    ]
    rows = []
    for metric in metrics:
        values = pd.to_numeric(replication_summary[metric], errors="coerce").dropna()
        if values.empty:
            continue
        rows.append(
            {
                "metric": metric,
                "mean": float(values.mean()),
                "p10": float(values.quantile(0.1)),
                "p90": float(values.quantile(0.9)),
            }
        )
    return pd.DataFrame(rows)


def run_simulation(visits: pd.DataFrame, scenario: ScenarioConfig) -> SimulationOutput:
    """Run all scenario replications and produce app-ready tables."""

    baseline = estimate_baseline_parameters(visits)
    frames = [run_single_replication(baseline, scenario, rep) for rep in range(scenario.replications)]
    patients = pd.concat(frames, ignore_index=True)
    summary = summarize_replications(patients)
    queue = queue_lengths_over_time(patients, scenario.horizon_hours)
    bottlenecks = bottleneck_shift_analysis(patients)
    return SimulationOutput(summary=summary, patients=patients, queue_lengths=queue, bottlenecks=bottlenecks)

