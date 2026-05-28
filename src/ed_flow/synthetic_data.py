"""Synthetic data generation for the external local prototype."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from ed_flow.config import DEFAULT_DATA_DIR
from ed_flow.data_contracts import TB_ED_VISITS_COLUMNS
from ed_flow.utils import weighted_choice


FACILITIES = [
    {
        "name": "Stollery Children's Hospital",
        "code": "SCH",
        "zone": "Edmonton",
        "corridor": "North",
        "peer": "Pediatric Academic",
        "department": "ED",
        "municipality": "Edmonton",
        "operator": "AHS",
        "abbreviation": "STOLLERY",
        "pediatric_weight": 0.92,
    },
    {
        "name": "Alberta Children's Hospital",
        "code": "ACH",
        "zone": "Calgary",
        "corridor": "South",
        "peer": "Pediatric Academic",
        "department": "ED",
        "municipality": "Calgary",
        "operator": "AHS",
        "abbreviation": "ACH",
        "pediatric_weight": 0.9,
    },
    {
        "name": "Royal Alexandra Hospital",
        "code": "RAH",
        "zone": "Edmonton",
        "corridor": "North",
        "peer": "Urban Tertiary",
        "department": "ED",
        "municipality": "Edmonton",
        "operator": "AHS",
        "abbreviation": "RAH",
        "pediatric_weight": 0.12,
    },
    {
        "name": "Foothills Medical Centre",
        "code": "FMC",
        "zone": "Calgary",
        "corridor": "South",
        "peer": "Urban Tertiary",
        "department": "ED",
        "municipality": "Calgary",
        "operator": "AHS",
        "abbreviation": "FMC",
        "pediatric_weight": 0.1,
    },
    {
        "name": "Red Deer Regional Hospital Centre",
        "code": "RDRH",
        "zone": "Central",
        "corridor": "Central",
        "peer": "Regional",
        "department": "ED",
        "municipality": "Red Deer",
        "operator": "AHS",
        "abbreviation": "RDRHC",
        "pediatric_weight": 0.18,
    },
    {
        "name": "Northeast Community Health Centre",
        "code": "NECHC",
        "zone": "Edmonton",
        "corridor": "North",
        "peer": "Urban Community",
        "department": "UCC",
        "municipality": "Edmonton",
        "operator": "AHS",
        "abbreviation": "NECHC",
        "pediatric_weight": 0.24,
    },
    {
        "name": "South Calgary Ambulatory Care Centre",
        "code": "SCACC",
        "zone": "Calgary",
        "corridor": "South",
        "peer": "Ambulatory",
        "department": "AACC",
        "municipality": "Calgary",
        "operator": "AHS",
        "abbreviation": "SCACC",
        "pediatric_weight": 0.2,
    },
]

AGE_GROUPS = ["Newborn", "Neonate", "Paediatric", "Adult", "Senior", "Unknown"]
PRESENTING_COMPLAINTS = [
    "Fever",
    "Respiratory distress",
    "Abdominal pain",
    "Mental health crisis",
    "Minor injury",
    "Head injury",
    "Vomiting/dehydration",
    "Chest pain",
    "Seizure",
    "Allergic reaction",
    "Medication concern",
    "Wound check",
]
ARRIVAL_MODES = ["Walk-in", "EMS", "Police", "Interfacility transfer", "Air ambulance"]
DISPOSITIONS = ["Admitted", "Discharged", "LWBS", "LAMA", "Died", "Transferred", "Recall", "Referred", "Active"]
SYNTHETIC_NOW = datetime(2026, 5, 28, 8, 0, 0)


def _age_for_group(rng: np.random.Generator, age_group: str) -> int:
    if age_group == "Newborn":
        return 0
    if age_group == "Neonate":
        return 0
    if age_group == "Paediatric":
        return int(rng.integers(1, 18))
    if age_group == "Adult":
        return int(rng.integers(18, 65))
    if age_group == "Senior":
        return int(rng.integers(65, 96))
    return int(rng.integers(0, 90))


def _age_group_for_facility(rng: np.random.Generator, facility: dict[str, object]) -> str:
    peds = float(facility["pediatric_weight"])
    if rng.random() < peds:
        return weighted_choice(rng, ["Newborn", "Neonate", "Paediatric"], [0.04, 0.06, 0.9])
    return weighted_choice(rng, ["Adult", "Senior", "Unknown"], [0.72, 0.24, 0.04])


def _arrival_datetime(rng: np.random.Generator) -> datetime:
    start = datetime(2025, 11, 1, 0, 0, 0)
    days = int(rng.integers(0, 205))
    hour = int(rng.choice(range(24), p=_hour_probabilities()))
    minute = int(rng.integers(0, 60))
    return start + timedelta(days=days, hours=hour, minutes=minute)


def _hour_probabilities() -> np.ndarray:
    weights = np.array(
        [
            0.35,
            0.25,
            0.2,
            0.18,
            0.2,
            0.28,
            0.45,
            0.7,
            0.9,
            1.0,
            1.05,
            1.12,
            1.25,
            1.3,
            1.38,
            1.45,
            1.5,
            1.55,
            1.5,
            1.35,
            1.1,
            0.9,
            0.65,
            0.45,
        ]
    )
    return weights / weights.sum()


def _triage_level(rng: np.random.Generator, complaint: str, arrival_mode: str) -> int:
    if complaint in {"Respiratory distress", "Seizure", "Allergic reaction"} or arrival_mode == "Air ambulance":
        weights = [0.08, 0.28, 0.42, 0.17, 0.05]
    elif complaint in {"Mental health crisis", "Chest pain", "Head injury"} or arrival_mode == "EMS":
        weights = [0.03, 0.18, 0.48, 0.24, 0.07]
    elif complaint in {"Minor injury", "Wound check", "Medication concern"}:
        weights = [0.0, 0.02, 0.2, 0.45, 0.33]
    else:
        weights = [0.01, 0.09, 0.43, 0.34, 0.13]
    return int(rng.choice([1, 2, 3, 4, 5], p=np.array(weights) / np.sum(weights)))


def _disposition(rng: np.random.Generator, triage: int, age_group: str, department_type: str) -> str:
    if department_type in {"UCC", "AACC"}:
        labels = ["Admitted", "Discharged", "LWBS", "LAMA", "Transferred", "Referred", "Recall"]
        weights = [0.04, 0.78, 0.08, 0.02, 0.04, 0.03, 0.01]
    elif triage <= 2:
        labels = ["Admitted", "Discharged", "LWBS", "LAMA", "Died", "Transferred", "Referred"]
        weights = [0.42, 0.44, 0.02, 0.02, 0.01, 0.07, 0.02]
    elif triage == 3:
        labels = ["Admitted", "Discharged", "LWBS", "LAMA", "Transferred", "Referred", "Recall"]
        weights = [0.22, 0.62, 0.07, 0.03, 0.03, 0.02, 0.01]
    else:
        labels = ["Admitted", "Discharged", "LWBS", "LAMA", "Transferred", "Referred", "Recall"]
        weights = [0.06, 0.76, 0.11, 0.03, 0.01, 0.02, 0.01]
    if age_group in {"Newborn", "Neonate"}:
        weights[0] = weights[0] * 1.4
        weights[1] = weights[1] * 0.9
    return weighted_choice(rng, labels, weights)


def _duration_minutes(rng: np.random.Generator, median: float, sigma: float, minimum: float, maximum: float) -> float:
    value = float(rng.lognormal(mean=np.log(max(median, 0.1)), sigma=sigma))
    return float(np.clip(value, minimum, maximum))


def generate_synthetic_ed_visits(n_visits: int = 1800, seed: int = 42) -> pd.DataFrame:
    """Generate a TB_ED_VISITS-shaped synthetic dataframe."""

    rng = np.random.default_rng(seed)
    records: list[dict[str, object]] = []
    for i in range(n_visits):
        facility = FACILITIES[int(rng.integers(0, len(FACILITIES)))]
        complaint = weighted_choice(
            rng,
            PRESENTING_COMPLAINTS,
            [1.0, 0.78, 0.86, 0.42, 1.25, 0.52, 0.66, 0.38, 0.28, 0.25, 0.22, 0.36],
        )
        arrival_mode = weighted_choice(rng, ARRIVAL_MODES, [0.76, 0.18, 0.01, 0.04, 0.01])
        triage = _triage_level(rng, complaint, arrival_mode)
        age_group = _age_group_for_facility(rng, facility)
        age = _age_for_group(rng, age_group)
        disposition = _disposition(rng, triage, age_group, str(facility["department"]))
        scheduled_flag = "Y" if rng.random() < 0.025 else "N"
        invalid_flag = "Y" if rng.random() < 0.025 else "N"

        first_contact = _arrival_datetime(rng)
        registration = first_contact + timedelta(minutes=_duration_minutes(rng, 8, 0.45, 1, 45))
        triage_dt = registration + timedelta(minutes=_duration_minutes(rng, 11, 0.55, 2, 75))
        if arrival_mode == "EMS":
            ems_offload = first_contact + timedelta(
                minutes=_duration_minutes(rng, 28 if triage >= 3 else 12, 0.7, 3, 180)
            )
        else:
            ems_offload = pd.NaT
        wait_room = _duration_minutes(
            rng,
            median={1: 4, 2: 18, 3: 55, 4: 95, 5: 125}[triage],
            sigma=0.75,
            minimum=0,
            maximum=420,
        )
        roomed = triage_dt + timedelta(minutes=wait_room)
        physician_wait = _duration_minutes(
            rng,
            median={1: 6, 2: 18, 3: 42, 4: 65, 5: 82}[triage],
            sigma=0.65,
            minimum=0,
            maximum=300,
        )
        pia = roomed + timedelta(minutes=physician_wait)
        consult_probability = 0.08 + (0.17 if triage <= 3 else 0.02) + (0.14 if disposition == "Admitted" else 0.0)
        has_consult = rng.random() < consult_probability
        consult_request = (
            pia + timedelta(minutes=_duration_minutes(rng, 55, 0.7, 8, 360)) if has_consult else pd.NaT
        )
        consult_completed = (
            consult_request + timedelta(minutes=_duration_minutes(rng, 130, 0.62, 25, 600))
            if has_consult
            else pd.NaT
        )
        treatment_anchor = consult_completed if has_consult else pia
        treatment_minutes = _duration_minutes(
            rng,
            median={1: 210, 2: 175, 3: 140, 4: 82, 5: 58}[triage],
            sigma=0.7,
            minimum=20,
            maximum=720,
        )
        disposition_dt = treatment_anchor + timedelta(minutes=treatment_minutes)
        decision_to_admit = pd.NaT
        bed_assign = pd.NaT
        if disposition == "Admitted":
            decision_to_admit = disposition_dt - timedelta(minutes=_duration_minutes(rng, 25, 0.4, 5, 90))
            bed_assign = decision_to_admit + timedelta(minutes=_duration_minutes(rng, 220, 0.7, 25, 980))
            depart = bed_assign + timedelta(minutes=_duration_minutes(rng, 45, 0.4, 10, 180))
        elif disposition == "Transferred":
            depart = disposition_dt + timedelta(minutes=_duration_minutes(rng, 165, 0.72, 20, 720))
        elif disposition == "LWBS":
            disposition_dt = triage_dt + timedelta(minutes=_duration_minutes(rng, 115, 0.8, 8, 480))
            depart = disposition_dt
            roomed = pd.NaT if rng.random() < 0.82 else roomed
            pia = pd.NaT if rng.random() < 0.7 else pia
            if pd.notna(roomed) and roomed > disposition_dt:
                roomed = pd.NaT
            if pd.notna(pia) and pia > disposition_dt:
                pia = pd.NaT
        elif disposition == "Active":
            depart = pd.NaT
        else:
            depart = disposition_dt + timedelta(minutes=_duration_minutes(rng, 32, 0.55, 3, 240))

        last_contact = depart if pd.notna(depart) else disposition_dt
        initial_location = min(
            [d for d in [roomed, ems_offload, triage_dt] if pd.notna(d)],
            default=triage_dt,
        )
        last_location = last_contact if pd.notna(last_contact) else initial_location

        if invalid_flag == "Y" and pd.notna(depart):
            if rng.random() < 0.5:
                depart = first_contact - timedelta(minutes=int(rng.integers(5, 90)))
            else:
                triage_dt = pd.NaT
        los_hrs = (
            (depart - first_contact).total_seconds() / 3600
            if pd.notna(depart) and pd.notna(first_contact)
            else np.nan
        )
        diagnosis = {
            "Fever": "Viral syndrome",
            "Respiratory distress": "Bronchiolitis/asthma spectrum",
            "Abdominal pain": "Abdominal pain, uncertain cause",
            "Mental health crisis": "Mental health assessment",
            "Minor injury": "Soft tissue injury",
            "Head injury": "Minor head injury",
            "Vomiting/dehydration": "Dehydration",
            "Chest pain": "Chest pain under investigation",
            "Seizure": "Seizure disorder",
            "Allergic reaction": "Allergic reaction",
            "Medication concern": "Medication adverse effect",
            "Wound check": "Wound reassessment",
        }[complaint]
        admitted_within = "Y" if disposition == "Admitted" and pd.notna(los_hrs) and los_hrs <= 8 else "N"
        discharged_within = "Y" if disposition == "Discharged" and pd.notna(los_hrs) and los_hrs <= 4 else "N"
        chart = f"SYN-MRN-{100000 + i:06d}"
        record = {
            "DATA_RECORD_ID": f"SYN-ED-{i + 1:07d}",
            "DATA_SOURCE": "SYNTHETIC",
            "DATA_SEQUENCE": i + 1,
            "SEQNUM_DAD": f"SYN-DAD-{i + 1:07d}" if disposition == "Admitted" else "",
            "SEQNUM_NACRS": f"SYN-NACRS-{i + 1:07d}",
            "DEPARTMENT_TYPE": facility["department"],
            "ENCOUNTER_NO_LEGACY": f"SYN-ENC-{900000 + i}",
            "CLNT_ENCTR_CSN_ID": f"SYN-CSN-{800000 + i}",
            "FISCAL_YEAR": "2025/26",
            "FISCAL_QUARTER": f"Q{((first_contact.month - 1) // 3) + 1}",
            "INSTITUTION_CODE": facility["code"],
            "INSTITUTION_NAME": facility["name"],
            "INSTITUTION_PEER_GROUP": facility["peer"],
            "INSTITUTION_ZONE_CODE": str(facility["zone"]).upper()[:3],
            "INSTITUTION_ZONE_NAME": facility["zone"],
            "INSTITUTION_POSTALCODE": "SYN-POSTAL",
            "INSTITUTION_CORRIDOR_CODE": str(facility["corridor"]).upper()[:3],
            "INSTITUTION_CORRIDOR_NAME": facility["corridor"],
            "INSTITUTION_TOP_14_FLAG": "Y" if facility["department"] == "ED" else "N",
            "INSTITUTION_TOP_16_FLAG": "Y" if facility["department"] == "ED" else "N",
            "INSTITUTION_TOP_17_FLAG": "Y" if facility["department"] == "ED" else "N",
            "SCHEDULED_ED_VISIT_FLAG": scheduled_flag,
            "ARRIVAL_MODE": arrival_mode,
            "TRIAGE_LEVEL": triage,
            "DISPOSITION_CODE": disposition[:3].upper(),
            "DISPOSITION_DESCRIPTION": disposition,
            "DISPOSITION_GROUP": disposition,
            "DISPOSITION_PERFORMANCE_REPORT": disposition,
            "PRESENTING_COMPLAINT": complaint,
            "DIAGNOSIS_DESCRIPTION": diagnosis,
            "PRIMARY_ADMIT_DIAGNOSIS": diagnosis if disposition == "Admitted" else "",
            "ADMIT_PATIENT_SERVICE_CODE": "SYN-PEDS" if age_group in {"Newborn", "Neonate", "Paediatric"} else "SYN-MED",
            "ADMIT_PATIENT_SERVICE_DESCRIPTION": "Synthetic Pediatrics" if disposition == "Admitted" else "",
            "ADMIT_UNIT_ID": "SYN-UNIT" if disposition == "Admitted" else "",
            "ADMIT_UNIT_NAME": "Synthetic Inpatient Unit" if disposition == "Admitted" else "",
            "ADMIT_UNIT_SPECIALTY": "Pediatrics" if age_group in {"Newborn", "Neonate", "Paediatric"} else "Medicine",
            "PATIENT_ID": f"SYN-PAT-{300000 + i}",
            "PATIENT_PHN": f"SYN-PHN-{400000 + i}",
            "PATIENT_SEX": weighted_choice(rng, ["Female", "Male", "X", "Unknown"], [0.49, 0.49, 0.01, 0.01]),
            "PATIENT_BIRTHDATE": "SYNTHETIC_ONLY",
            "PATIENT_DEATH_DATE": "",
            "PATIENT_AGE": age,
            "PATIENT_AGE_GROUP": age_group,
            "PATIENT_CHART": chart,
            "PATIENT_ULI": f"SYN-ULI-{500000 + i}",
            "PATIENT_POSTALCODE": "SYN-POSTAL",
            "PATIENT_CORRIDOR_CODE": str(facility["corridor"]).upper()[:3],
            "PATIENT_CORRIDOR_NAME": facility["corridor"],
            "PATIENT_ZONE_CODE": str(facility["zone"]).upper()[:3],
            "PATIENT_ZONE_NAME": facility["zone"],
            "FIRST_CONTACT_DATETIME": first_contact,
            "REGISTRATION_DATETIME": registration,
            "TRIAGE_DATETIME": triage_dt,
            "EMS_OFFLOAD_DATETIME": ems_offload,
            "INITIAL_LOCATION_DATETIME": initial_location,
            "INITIAL_ROOMED_IN_DATETIME": roomed,
            "PHYSICIAN_INITIAL_ASSESSMENT_DATETIME": pia,
            "INITIAL_PHYSICIAN_CONSULT_REQUEST_DATETIME": consult_request,
            "INITIAL_PHYSICIAN_CONSULT_COMPLETED_DATETIME": consult_completed,
            "DISPOSITION_DATETIME": disposition_dt,
            "DECISION_TO_ADMIT_DATETIME": decision_to_admit,
            "IP_BED_ASSIGN_DATETIME": bed_assign,
            "DEPART_ED_DATETIME": depart,
            "LAST_CONTACT_DATETIME": last_contact,
            "INITIAL_ROOMED_IN_LOCATION_DESCRIPTION": f"{facility['abbreviation']} synthetic room",
            "INITIAL_ROOMED_IN_LOCATION_ID": f"SYN-LOC-{int(rng.integers(1, 80)):03d}",
            "LOCATION_ID_COUNT": int(rng.integers(1, 5)),
            "LAST_LOCATION_DESCRIPTION": f"{facility['abbreviation']} synthetic final location",
            "LAST_LOCATION_DATETIME": last_location,
            "INITIAL_PHYSICIAN_CONSULT_PROVIDER_ID": "SYN-CONSULT-PROV" if has_consult else "",
            "INITIAL_PHYSICIAN_CONSULT_PROVIDER_TYPE_NAME": "Synthetic specialist" if has_consult else "",
            "INITIAL_PHYSICIAN_CONSULT_SPECIALTY_NAME": weighted_choice(
                rng, ["Pediatrics", "Surgery", "Medicine", "Mental Health", "Orthopedics"], [0.45, 0.16, 0.2, 0.12, 0.07]
            )
            if has_consult
            else "",
            "CONSULT_COUNT": int(rng.integers(1, 3)) if has_consult else 0,
            "INVALID_LOS_CALC_FLAG": invalid_flag,
            "ADMITTED_WITHIN_8HRS_FLAG": admitted_within,
            "DISCHARGED_WITHIN_4HRS_FLAG": discharged_within,
            "ED_LOS_HRS": los_hrs,
            "ED_LOS_ADMITTED_HRS": los_hrs if disposition == "Admitted" else np.nan,
            "ED_LOS_DISCHARGED_HRS": los_hrs if disposition == "Discharged" else np.nan,
            "ED_LOS_FIRST_CONTACT_TO_EMS_HANDOFF_MINS": (
                (ems_offload - first_contact).total_seconds() / 60 if pd.notna(ems_offload) else np.nan
            ),
            "ED_LOS_FIRST_CONTACT_TO_INITIAL_ROOMED_IN_ED_HRS": (
                (roomed - first_contact).total_seconds() / 3600 if pd.notna(roomed) else np.nan
            ),
            "ED_LOS_FIRST_CONTACT_TO_PHYSICIAN_INITIAL_ASSESSMENT_HRS": (
                (pia - first_contact).total_seconds() / 3600 if pd.notna(pia) else np.nan
            ),
            "ED_LOS_PHYSICIAN_INITIAL_ASSESSMENT_TO_PHYSICIAN_INITIAL_CONSULT_REQUEST_HRS": (
                (consult_request - pia).total_seconds() / 3600
                if pd.notna(consult_request) and pd.notna(pia)
                else np.nan
            ),
            "ED_LOS_PHYSICIAN_INITIAL_ASSESSMENT_TO_DISPOSITION_HRS": (
                (disposition_dt - pia).total_seconds() / 3600 if pd.notna(disposition_dt) and pd.notna(pia) else np.nan
            ),
            "ED_LOS_PHYSICIAN_INITIAL_CONSULT_REQUEST_TO_DISPOSITION_HRS": (
                (disposition_dt - consult_request).total_seconds() / 3600
                if pd.notna(disposition_dt) and pd.notna(consult_request)
                else np.nan
            ),
            "ED_LOS_DECISION_TO_ADMIT_TO_LAST_CONTACT_HRS": (
                (last_contact - decision_to_admit).total_seconds() / 3600
                if pd.notna(last_contact) and pd.notna(decision_to_admit)
                else np.nan
            ),
            "ROW_CREATE_DATETIME": first_contact + timedelta(days=1),
            "ROW_UPDATE_DATETIME": min(SYNTHETIC_NOW, first_contact + timedelta(days=int(rng.integers(1, 7)))),
            "INSTITUTION_MUNICIPALITY": facility["municipality"],
            "INSTITUTION_OPERATOR": facility["operator"],
            "INSTITUTION_ABBREVIATION": facility["abbreviation"],
            "PATIENT_MUNICIPALITY": weighted_choice(
                rng, ["Synthetic Edmonton", "Synthetic Calgary", "Synthetic Rural North", "Synthetic Rural South"], [0.35, 0.35, 0.15, 0.15]
            ),
        }
        records.append(record)

    df = pd.DataFrame.from_records(records)
    for column in TB_ED_VISITS_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df.loc[:, TB_ED_VISITS_COLUMNS]


def generate_waiting_room_patients(visits: pd.DataFrame, seed: int = 43, n: int = 40) -> pd.DataFrame:
    """Generate active waiting-room registry rows linked to synthetic MRNs."""

    rng = np.random.default_rng(seed)
    peds = visits[visits["PATIENT_AGE_GROUP"].isin(["Newborn", "Neonate", "Paediatric"])].copy()
    sample = peds.sample(n=min(n, len(peds)), random_state=seed).reset_index(drop=True)
    stages = [
        "waiting_to_triage",
        "triaged_waiting",
        "roomed_not_seen",
        "waiting_for_physician_initial_assessment",
        "consult_delay",
        "decision_to_admit_boarder",
        "ems_offload_delay",
    ]
    records = []
    for idx, row in sample.iterrows():
        stage = weighted_choice(rng, stages, [0.16, 0.24, 0.18, 0.14, 0.11, 0.1, 0.07])
        arrived = SYNTHETIC_NOW - timedelta(minutes=int(rng.integers(15, 560)))
        records.append(
            {
                "mrn": row["PATIENT_CHART"],
                "facility": row["INSTITUTION_NAME"],
                "synthetic_patient_name": f"Synthetic Patient {idx + 1:02d}",
                "age": row["PATIENT_AGE"],
                "age_group": row["PATIENT_AGE_GROUP"],
                "sex": row["PATIENT_SEX"],
                "triage_level": int(row["TRIAGE_LEVEL"]),
                "presenting_complaint": row["PRESENTING_COMPLAINT"],
                "arrival_mode": row["ARRIVAL_MODE"],
                "current_stage": stage,
                "arrival_datetime": arrived,
                "last_event_datetime": arrived + timedelta(minutes=int(rng.integers(3, 120))),
                "lwbs_risk": round(float(np.clip(rng.beta(2.0, 8.0) + (0.07 if stage == "triaged_waiting" else 0), 0, 0.85)), 3),
                "source": "synthetic_waiting_room_registry",
            }
        )
    return pd.DataFrame.from_records(records)


def generate_chart_notes(waiting_room: pd.DataFrame, seed: int = 44) -> pd.DataFrame:
    """Generate clearly synthetic chart-review source snippets."""

    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    section_templates = {
        "ed_provider_notes": "Synthetic ED note: assessed for {complaint}; no real patient information; plan reflects simulated operational context.",
        "encounter_notes": "Synthetic encounter note: triage category {triage}; reassessment timing and queue status are simulated.",
        "consult_notes": "Synthetic consult note: service asked to review; response timing is part of synthetic delay modelling.",
        "admission_hp_notes": "Synthetic admission H&P: provisional working diagnosis tied to {complaint}; bed request is simulated.",
        "imaging": "Synthetic imaging result: no critical real finding; sample narrative created for prototype testing.",
        "labs": "Synthetic lab comment: example result-comment text only; values are not patient data.",
        "problem_list": "Synthetic active problem: history element included to test summarization sections.",
        "medical_history": "Synthetic medical history: prior condition text generated for demo only.",
        "referrals": "Synthetic referral context: referral workflow example with no real provider or patient details.",
    }
    for _, patient in waiting_room.iterrows():
        for source_type, template in section_templates.items():
            if rng.random() < 0.18 and source_type not in {"ed_provider_notes", "encounter_notes"}:
                continue
            count = int(rng.integers(1, 3))
            for line in range(count):
                contact = pd.to_datetime(patient["arrival_datetime"]) - timedelta(days=int(rng.integers(0, 90)), hours=int(rng.integers(0, 12)))
                rows.append(
                    {
                        "mrn": patient["mrn"],
                        "source_type": source_type,
                        "department_name": patient["facility"],
                        "note_id": f"SYN-NOTE-{patient['mrn']}-{source_type}-{line}",
                        "note_text": template.format(
                            complaint=patient["presenting_complaint"],
                            triage=patient["triage_level"],
                        ),
                        "contact_datetime": contact,
                        "updated_datetime": contact + timedelta(hours=int(rng.integers(1, 72))),
                    }
                )
    return pd.DataFrame.from_records(rows)


def generate_expanded_flow_events(waiting_room: pd.DataFrame, seed: int = 45) -> pd.DataFrame:
    """Generate synthetic real-time flow events for the expanded module."""

    rng = np.random.default_rng(seed)
    event_types = [
        "location_update",
        "bed_request",
        "bed_assigned",
        "bed_cleaning_started",
        "bed_cleaning_completed",
        "diagnostic_ordered",
        "diagnostic_resulted",
        "consult_requested",
        "consult_completed",
        "transport_requested",
    ]
    rows = []
    for _, patient in waiting_room.iterrows():
        base = pd.to_datetime(patient["arrival_datetime"])
        for step in range(int(rng.integers(3, 8))):
            event = weighted_choice(rng, event_types, [0.2, 0.09, 0.08, 0.06, 0.06, 0.15, 0.13, 0.12, 0.08, 0.03])
            rows.append(
                {
                    "event_id": f"SYN-EVENT-{len(rows) + 1:06d}",
                    "mrn": patient["mrn"],
                    "facility": patient["facility"],
                    "event_type": event,
                    "event_datetime": base + timedelta(minutes=int(rng.integers(5, 420))),
                    "location": f"Zone {int(rng.integers(1, 6))}",
                    "service": weighted_choice(rng, ["Pediatrics", "Emergency", "Surgery", "Medicine", "Mental Health"], [0.42, 0.3, 0.08, 0.12, 0.08]),
                    "constraint_flag": "Y" if rng.random() < 0.18 else "N",
                    "synthetic_detail": f"Synthetic {event.replace('_', ' ')} event",
                }
            )
    return pd.DataFrame.from_records(rows)


def generate_beds_staffing_diagnostics(waiting_room: pd.DataFrame, seed: int = 46) -> pd.DataFrame:
    """Generate synthetic capacity snapshots for the expanded module."""

    rng = np.random.default_rng(seed)
    facilities = sorted(waiting_room["facility"].unique())
    rows = []
    for facility in facilities:
        for h in range(0, 48):
            ts = SYNTHETIC_NOW + timedelta(hours=h)
            total_beds = int(rng.integers(26, 62))
            occupied = int(np.clip(rng.normal(total_beds * 0.86, 4), 0, total_beds))
            rows.append(
                {
                    "snapshot_datetime": ts,
                    "facility": facility,
                    "ed_treatment_spaces": total_beds,
                    "ed_occupied_spaces": occupied,
                    "inpatient_available_beds": int(rng.integers(0, 18)),
                    "pending_discharges": int(rng.integers(1, 26)),
                    "beds_cleaning": int(rng.integers(0, 8)),
                    "nurses_on_shift": int(rng.integers(12, 40)),
                    "physicians_on_shift": int(rng.integers(3, 14)),
                    "consult_queue": int(rng.integers(0, 16)),
                    "lab_median_tat_minutes": int(rng.integers(42, 130)),
                    "imaging_median_tat_minutes": int(rng.integers(55, 190)),
                    "ems_arrivals_expected": int(rng.integers(0, 10)),
                    "transfer_requests_waiting": int(rng.integers(0, 7)),
                    "synthetic_assumption": "Expanded operational feed is synthetic and assumption-based.",
                }
            )
    return pd.DataFrame.from_records(rows)


def write_synthetic_data(data_dir: Path = DEFAULT_DATA_DIR, force: bool = False) -> dict[str, Path]:
    """Write all synthetic CSV deliverables and return their paths."""

    data_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "visits": data_dir / "synthetic_ed_visits.csv",
        "waiting_room": data_dir / "synthetic_waiting_room_patients.csv",
        "chart_notes": data_dir / "synthetic_chart_notes.csv",
        "expanded_events": data_dir / "synthetic_expanded_flow_events.csv",
        "beds_staffing": data_dir / "synthetic_beds_staffing_diagnostics.csv",
    }
    if not force and all(path.exists() for path in paths.values()):
        return paths

    visits = generate_synthetic_ed_visits()
    waiting_room = generate_waiting_room_patients(visits)
    chart_notes = generate_chart_notes(waiting_room)
    expanded_events = generate_expanded_flow_events(waiting_room)
    beds_staffing = generate_beds_staffing_diagnostics(waiting_room)

    visits.to_csv(paths["visits"], index=False)
    waiting_room.to_csv(paths["waiting_room"], index=False)
    chart_notes.to_csv(paths["chart_notes"], index=False)
    expanded_events.to_csv(paths["expanded_events"], index=False)
    beds_staffing.to_csv(paths["beds_staffing"], index=False)
    return paths


def ensure_synthetic_data(data_dir: Path = DEFAULT_DATA_DIR) -> dict[str, Path]:
    """Create synthetic data if any expected file is missing."""

    return write_synthetic_data(data_dir=data_dir, force=False)


if __name__ == "__main__":
    written = write_synthetic_data(force=True)
    for label, path in written.items():
        print(f"{label}: {path}")
