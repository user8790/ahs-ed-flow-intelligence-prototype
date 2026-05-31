"""Shared v2 constants."""

from __future__ import annotations

PEDIATRIC_AGE_GROUPS = ["Newborn", "Neonate", "Paediatric"]

V2_TAB_NAMES = [
    "Executive Command Centre",
    "Alberta Public Pressure Map & Site Explorer",
    "Public ED Wait Times Monitor",
    "Pediatric Respiratory Surge",
    "Smoke, Heat, Weather & Air Quality Stress",
    "Travel Friction & Access Disruption",
    "Public Scenario Workbench",
    "TB_ED_VISITS Internal-Ready Flow Analytics",
    "Waiting Room MRN Chart Summaries",
    "Hybrid Forecasting Lab",
    "Simulation Lab",
    "Bed, Boarding, Discharge & Transfer Intelligence",
    "Staffing & Resource Sensitivity",
    "Model Validation, Calibration & Governance",
    "Snowflake Porting & Day-One Internal Setup",
    "Data Linkages & Refresh Status",
]

SECURE_INTERNAL_DATASETS = [
    "TB_ED_VISITS",
    "real_time_ed_location_events",
    "adt_bed_board_status",
    "inpatient_census",
    "pending_discharges",
    "environmental_services_bed_cleaning",
    "nurse_physician_staffing_rosters",
    "consult_queues",
    "lab_imaging_turnaround",
    "transport_transfer_requests",
    "ems_arrival_estimates",
    "inpatient_unit_capacity",
    "service_team_assignment",
    "chart_review_semantic_views",
]
