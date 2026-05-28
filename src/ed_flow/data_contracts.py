"""Data contracts and typed objects shared across the prototype."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field


TB_ED_VISITS_COLUMNS: list[str] = [
    "DATA_RECORD_ID",
    "DATA_SOURCE",
    "DATA_SEQUENCE",
    "SEQNUM_DAD",
    "SEQNUM_NACRS",
    "DEPARTMENT_TYPE",
    "ENCOUNTER_NO_LEGACY",
    "CLNT_ENCTR_CSN_ID",
    "FISCAL_YEAR",
    "FISCAL_QUARTER",
    "INSTITUTION_CODE",
    "INSTITUTION_NAME",
    "INSTITUTION_PEER_GROUP",
    "INSTITUTION_ZONE_CODE",
    "INSTITUTION_ZONE_NAME",
    "INSTITUTION_POSTALCODE",
    "INSTITUTION_CORRIDOR_CODE",
    "INSTITUTION_CORRIDOR_NAME",
    "INSTITUTION_TOP_14_FLAG",
    "INSTITUTION_TOP_16_FLAG",
    "INSTITUTION_TOP_17_FLAG",
    "SCHEDULED_ED_VISIT_FLAG",
    "ARRIVAL_MODE",
    "TRIAGE_LEVEL",
    "DISPOSITION_CODE",
    "DISPOSITION_DESCRIPTION",
    "DISPOSITION_GROUP",
    "DISPOSITION_PERFORMANCE_REPORT",
    "PRESENTING_COMPLAINT",
    "DIAGNOSIS_DESCRIPTION",
    "PRIMARY_ADMIT_DIAGNOSIS",
    "ADMIT_PATIENT_SERVICE_CODE",
    "ADMIT_PATIENT_SERVICE_DESCRIPTION",
    "ADMIT_UNIT_ID",
    "ADMIT_UNIT_NAME",
    "ADMIT_UNIT_SPECIALTY",
    "PATIENT_ID",
    "PATIENT_PHN",
    "PATIENT_SEX",
    "PATIENT_BIRTHDATE",
    "PATIENT_DEATH_DATE",
    "PATIENT_AGE",
    "PATIENT_AGE_GROUP",
    "PATIENT_CHART",
    "PATIENT_ULI",
    "PATIENT_POSTALCODE",
    "PATIENT_CORRIDOR_CODE",
    "PATIENT_CORRIDOR_NAME",
    "PATIENT_ZONE_CODE",
    "PATIENT_ZONE_NAME",
    "FIRST_CONTACT_DATETIME",
    "REGISTRATION_DATETIME",
    "TRIAGE_DATETIME",
    "EMS_OFFLOAD_DATETIME",
    "INITIAL_LOCATION_DATETIME",
    "INITIAL_ROOMED_IN_DATETIME",
    "PHYSICIAN_INITIAL_ASSESSMENT_DATETIME",
    "INITIAL_PHYSICIAN_CONSULT_REQUEST_DATETIME",
    "INITIAL_PHYSICIAN_CONSULT_COMPLETED_DATETIME",
    "DISPOSITION_DATETIME",
    "DECISION_TO_ADMIT_DATETIME",
    "IP_BED_ASSIGN_DATETIME",
    "DEPART_ED_DATETIME",
    "LAST_CONTACT_DATETIME",
    "INITIAL_ROOMED_IN_LOCATION_DESCRIPTION",
    "INITIAL_ROOMED_IN_LOCATION_ID",
    "LOCATION_ID_COUNT",
    "LAST_LOCATION_DESCRIPTION",
    "LAST_LOCATION_DATETIME",
    "INITIAL_PHYSICIAN_CONSULT_PROVIDER_ID",
    "INITIAL_PHYSICIAN_CONSULT_PROVIDER_TYPE_NAME",
    "INITIAL_PHYSICIAN_CONSULT_SPECIALTY_NAME",
    "CONSULT_COUNT",
    "INVALID_LOS_CALC_FLAG",
    "ADMITTED_WITHIN_8HRS_FLAG",
    "DISCHARGED_WITHIN_4HRS_FLAG",
    "ED_LOS_HRS",
    "ED_LOS_ADMITTED_HRS",
    "ED_LOS_DISCHARGED_HRS",
    "ED_LOS_FIRST_CONTACT_TO_EMS_HANDOFF_MINS",
    "ED_LOS_FIRST_CONTACT_TO_INITIAL_ROOMED_IN_ED_HRS",
    "ED_LOS_FIRST_CONTACT_TO_PHYSICIAN_INITIAL_ASSESSMENT_HRS",
    "ED_LOS_PHYSICIAN_INITIAL_ASSESSMENT_TO_PHYSICIAN_INITIAL_CONSULT_REQUEST_HRS",
    "ED_LOS_PHYSICIAN_INITIAL_ASSESSMENT_TO_DISPOSITION_HRS",
    "ED_LOS_PHYSICIAN_INITIAL_CONSULT_REQUEST_TO_DISPOSITION_HRS",
    "ED_LOS_DECISION_TO_ADMIT_TO_LAST_CONTACT_HRS",
    "ROW_CREATE_DATETIME",
    "ROW_UPDATE_DATETIME",
    "INSTITUTION_MUNICIPALITY",
    "INSTITUTION_OPERATOR",
    "INSTITUTION_ABBREVIATION",
    "PATIENT_MUNICIPALITY",
]

SENSITIVE_COLUMNS: set[str] = {
    "PATIENT_ID",
    "PATIENT_PHN",
    "PATIENT_BIRTHDATE",
    "PATIENT_CHART",
    "PATIENT_ULI",
    "PATIENT_POSTALCODE",
}

CONSTRAINED_ANALYSIS_COLUMNS: list[str] = [
    column for column in TB_ED_VISITS_COLUMNS if column not in SENSITIVE_COLUMNS
]

SNOWFLAKE_SELECT_COLUMNS: list[str] = [
    "DATA_RECORD_ID",
    "DATA_SOURCE",
    "DEPARTMENT_TYPE",
    "INSTITUTION_NAME",
    "INSTITUTION_CODE",
    "INSTITUTION_ZONE_NAME",
    "INSTITUTION_CORRIDOR_NAME",
    "INSTITUTION_PEER_GROUP",
    "ARRIVAL_MODE",
    "TRIAGE_LEVEL",
    "DISPOSITION_GROUP",
    "DISPOSITION_PERFORMANCE_REPORT",
    "PRESENTING_COMPLAINT",
    "DIAGNOSIS_DESCRIPTION",
    "PRIMARY_ADMIT_DIAGNOSIS",
    "ADMIT_PATIENT_SERVICE_DESCRIPTION",
    "ADMIT_UNIT_NAME",
    "ADMIT_UNIT_SPECIALTY",
    "PATIENT_SEX",
    "PATIENT_AGE",
    "PATIENT_AGE_GROUP",
    "PATIENT_ZONE_NAME",
    "PATIENT_CORRIDOR_NAME",
    "FIRST_CONTACT_DATETIME",
    "REGISTRATION_DATETIME",
    "TRIAGE_DATETIME",
    "EMS_OFFLOAD_DATETIME",
    "INITIAL_LOCATION_DATETIME",
    "INITIAL_ROOMED_IN_DATETIME",
    "PHYSICIAN_INITIAL_ASSESSMENT_DATETIME",
    "INITIAL_PHYSICIAN_CONSULT_REQUEST_DATETIME",
    "INITIAL_PHYSICIAN_CONSULT_COMPLETED_DATETIME",
    "DISPOSITION_DATETIME",
    "DECISION_TO_ADMIT_DATETIME",
    "IP_BED_ASSIGN_DATETIME",
    "DEPART_ED_DATETIME",
    "LAST_CONTACT_DATETIME",
    "INITIAL_ROOMED_IN_LOCATION_DESCRIPTION",
    "LOCATION_ID_COUNT",
    "LAST_LOCATION_DESCRIPTION",
    "LAST_LOCATION_DATETIME",
    "INITIAL_PHYSICIAN_CONSULT_PROVIDER_TYPE_NAME",
    "INITIAL_PHYSICIAN_CONSULT_SPECIALTY_NAME",
    "CONSULT_COUNT",
    "ADMITTED_WITHIN_8HRS_FLAG",
    "DISCHARGED_WITHIN_4HRS_FLAG",
    "ED_LOS_HRS",
    "ED_LOS_ADMITTED_HRS",
    "ED_LOS_DISCHARGED_HRS",
    "ED_LOS_FIRST_CONTACT_TO_EMS_HANDOFF_MINS",
    "ED_LOS_FIRST_CONTACT_TO_INITIAL_ROOMED_IN_ED_HRS",
    "ED_LOS_FIRST_CONTACT_TO_PHYSICIAN_INITIAL_ASSESSMENT_HRS",
    "ED_LOS_PHYSICIAN_INITIAL_ASSESSMENT_TO_DISPOSITION_HRS",
    "ED_LOS_PHYSICIAN_INITIAL_CONSULT_REQUEST_TO_DISPOSITION_HRS",
    "ED_LOS_DECISION_TO_ADMIT_TO_LAST_CONTACT_HRS",
    "INSTITUTION_MUNICIPALITY",
    "INSTITUTION_OPERATOR",
    "INSTITUTION_ABBREVIATION",
    "PATIENT_MUNICIPALITY",
]

TIMESTAMP_COLUMNS: list[str] = [
    "FIRST_CONTACT_DATETIME",
    "REGISTRATION_DATETIME",
    "TRIAGE_DATETIME",
    "EMS_OFFLOAD_DATETIME",
    "INITIAL_LOCATION_DATETIME",
    "INITIAL_ROOMED_IN_DATETIME",
    "PHYSICIAN_INITIAL_ASSESSMENT_DATETIME",
    "INITIAL_PHYSICIAN_CONSULT_REQUEST_DATETIME",
    "INITIAL_PHYSICIAN_CONSULT_COMPLETED_DATETIME",
    "DISPOSITION_DATETIME",
    "DECISION_TO_ADMIT_DATETIME",
    "IP_BED_ASSIGN_DATETIME",
    "DEPART_ED_DATETIME",
    "LAST_CONTACT_DATETIME",
    "LAST_LOCATION_DATETIME",
    "ROW_CREATE_DATETIME",
    "ROW_UPDATE_DATETIME",
]

SEMANTIC_VIEW_COLUMNS: dict[str, list[str]] = {
    "SV_ADMISSION_HP_NOTES": [
        "DEPARTMENT_NAME",
        "FULL_NOTE",
        "NOTE_ID",
        "PAT_MRN_ID",
        "NOTE_CSN_ID",
        "CONTACT_DATE",
        "ENT_INST_LOCAL_DTTM",
        "UPD_AUT_LOCAL_DTTM",
    ],
    "SV_CONSULT_NOTES": [
        "DEPARTMENT_NAME",
        "NAME",
        "NOTE_ID",
        "NOTE_TEXT",
        "PAT_MRN_ID",
        "LINE",
        "NOTE_CSN_ID",
        "CONTACT_DATE",
        "ENT_INST_LOCAL_DTTM",
        "UPD_AUT_LOCAL_DTTM",
    ],
    "SV_IMAGING_NOTES": [
        "AUTHRZING_PROV_ID",
        "BILLING_PROV_ID",
        "DESCRIPTION",
        "NARRATIVE",
        "ORDER_PROC_ID",
        "PAT_ENC_CSN_ID",
        "PAT_ID",
        "PAT_MRN_ID",
        "PROC_ID",
        "RESULT_LAB_ID",
        "ORDERING_DATE",
    ],
    "SV_LAB_REPORTS": [
        "COMPONENT_ID",
        "DESCRIPTION",
        "NAME",
        "ORDER_PROC_ID",
        "PAT_ENC_CSN_ID",
        "PAT_ID",
        "PAT_MRN_ID",
        "PROC_ID",
        "RESULTS_COMP_CMT",
        "RESULT_LAB_ID",
        "ORDERING_DATE",
        "ORDER_TIME",
        "RESULT_TIME",
    ],
    "SV_ENC_NOTES": [
        "PAT_MRN_ID",
        "DEPARTMENT_NAME",
        "IP_NOTE_TYPE_C",
        "NOTE_CSN_ID",
        "NOTE_ID",
        "NOTE_TEXT",
        "CONTACT_DATE",
        "ENT_INST_LOCAL_DTTM",
        "UPD_AUT_LOCAL_DTTM",
    ],
    "SV_PROBLEM_LIST": [
        "DESCRIPTION",
        "DX_NAME",
        "PAT_ID",
        "PAT_MRN_ID",
        "PROBLEM_CMT",
        "PROBLEM_STATUS",
        "NOTED_DATE",
        "RESOLVED_DATE",
    ],
    "SV_MEDICAL_HISTORY": [
        "COMMENTS",
        "DX_NAME",
        "PAT_ENC_CSN_ID",
        "PAT_ID",
        "PAT_MRN_ID",
        "CONTACT_DATE",
    ],
    "SV_EDPROVIDER_NOTES": [
        "DEPARTMENT_NAME",
        "DX_NAME",
        "NOTE_CSN_ID",
        "NOTE_ID",
        "NOTE_TEXT",
        "PAT_ENC_CSN_ID",
        "PAT_MRN_ID",
        "CONTACT_DATE",
        "ENT_INST_LOCAL_DTTM",
        "UPD_AUT_LOCAL_DTTM",
    ],
    "SV_REFERRALS": [
        "DEPARTMENT_NAME",
        "PAT_ID",
        "PAT_MRN_ID",
        "PCP_PROV_ID",
        "PROV_NAME",
        "PROV_TYPE",
        "REASON_FOR_REFERRAL",
        "REFD_BY_DEPT_ID",
        "REFD_TO_DEPT_ID",
        "REFERRAL_CLASS",
        "REFERRAL_ID",
        "REFERRAL_PROV_ID",
        "REFERRAL_STATUS",
        "REFERRAL_TYPE",
        "REFERRING_DEPARTMENT",
        "REFERRING_PROV_ID",
        "SCHED_STATUS",
        "ENTRY_DATE",
        "EXP_DATE",
        "SERV_DATE",
        "START_DATE",
    ],
}


class VisitFilters(BaseModel):
    """Common visit filters used by local and Snowflake backends."""

    facility: str | None = None
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    pediatric_only: bool = False
    include_scheduled: bool = False
    include_invalid_los: bool = False
    age_groups: list[str] | None = None


class ScenarioConfig(BaseModel):
    """Scenario controls for the simulation lab."""

    facility: str
    horizon_hours: int = Field(default=24, ge=4, le=168)
    replications: int = Field(default=10, ge=1, le=200)
    random_seed: int = 42
    arrival_surge_multiplier: float = Field(default=1.0, ge=0.1, le=3.0)
    triage_capacity_delta: int = Field(default=0, ge=-5, le=10)
    physician_capacity_delta: int = Field(default=0, ge=-10, le=20)
    rooming_capacity_delta: int = Field(default=0, ge=-20, le=40)
    fast_track_enabled: bool = False
    consult_turnaround_improvement: float = Field(default=0.0, ge=0.0, le=0.75)
    diagnostic_turnaround_improvement: float = Field(default=0.0, ge=0.0, le=0.75)
    admission_bed_improvement: float = Field(default=0.0, ge=0.0, le=0.75)
    boarding_reduction: float = Field(default=0.0, ge=0.0, le=0.8)
    discharge_acceleration: float = Field(default=0.0, ge=0.0, le=0.5)
    ems_offload_improvement: float = Field(default=0.0, ge=0.0, le=0.75)


class ChartSection(BaseModel):
    """One chart-review source section."""

    name: str
    content: str
    freshness: datetime | None = None
    source_count: int = 0


class ChartContext(BaseModel):
    """Normalized chart context keyed by configurable MRN mapping."""

    mrn: str
    mapped_source_field: str = "PATIENT_CHART"
    sections: dict[str, ChartSection] = Field(default_factory=dict)
    demographics: dict[str, Any] = Field(default_factory=dict)
    freshness: datetime | None = None


class DataQualityReport(BaseModel):
    """Portable data quality summary for app display and tests."""

    row_count: int
    invalid_los_count: int
    missing_first_contact_count: int
    scheduled_visit_count: int
    max_row_update_datetime: datetime | None = None
    warnings: list[str] = Field(default_factory=list)


def assert_columns_available(df: pd.DataFrame, required: list[str]) -> None:
    """Raise a clear error if required columns are missing."""

    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def constrained_projection(df: pd.DataFrame) -> pd.DataFrame:
    """Return columns permitted for the constrained ED module."""

    cols = [column for column in CONSTRAINED_ANALYSIS_COLUMNS if column in df.columns]
    return df.loc[:, cols].copy()

