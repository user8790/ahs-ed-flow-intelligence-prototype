"""Local synthetic backend with the same public methods as SnowflakeBackend."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ed_flow.config import DEFAULT_DATA_DIR
from ed_flow.data_contracts import ChartContext, ChartSection, TIMESTAMP_COLUMNS, VisitFilters
from ed_flow.synthetic_data import ensure_synthetic_data
from ed_flow.utils import ensure_datetime


class LocalBackend:
    """Load and persist synthetic prototype data from CSV files."""

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR):
        self.data_dir = Path(data_dir)
        self.paths = ensure_synthetic_data(self.data_dir)

    def load_ed_visits(self, filters: VisitFilters | None = None) -> pd.DataFrame:
        """Load synthetic ED visits and apply the standard business rules."""

        df = pd.read_csv(self.paths["visits"])
        df = ensure_datetime(df, TIMESTAMP_COLUMNS)
        filters = filters or VisitFilters()
        if not filters.include_invalid_los and "INVALID_LOS_CALC_FLAG" in df:
            df = df[df["INVALID_LOS_CALC_FLAG"].fillna("N") != "Y"]
        if not filters.include_scheduled and "SCHEDULED_ED_VISIT_FLAG" in df:
            df = df[df["SCHEDULED_ED_VISIT_FLAG"].fillna("N") != "Y"]
        if filters.facility:
            df = df[df["INSTITUTION_NAME"] == filters.facility]
        if filters.pediatric_only:
            df = df[df["PATIENT_AGE_GROUP"].isin(["Newborn", "Neonate", "Paediatric"])]
        if filters.age_groups:
            df = df[df["PATIENT_AGE_GROUP"].isin(filters.age_groups)]
        if filters.start_datetime is not None:
            df = df[df["FIRST_CONTACT_DATETIME"] >= pd.Timestamp(filters.start_datetime)]
        if filters.end_datetime is not None:
            df = df[df["FIRST_CONTACT_DATETIME"] < pd.Timestamp(filters.end_datetime)]
        return df.reset_index(drop=True)

    def load_recent_ed_visits(self, filters: VisitFilters | None = None) -> pd.DataFrame:
        """Load a recent slice for command-centre displays."""

        df = self.load_ed_visits(filters)
        if df.empty:
            return df
        max_time = df["FIRST_CONTACT_DATETIME"].max()
        return df[df["FIRST_CONTACT_DATETIME"] >= max_time - pd.Timedelta(days=14)].reset_index(drop=True)

    def load_current_active_visits(self, filters: VisitFilters | None = None) -> pd.DataFrame:
        """Load the active synthetic waiting-room registry."""

        df = pd.read_csv(self.paths["waiting_room"])
        df = ensure_datetime(df, ["arrival_datetime", "last_event_datetime"])
        filters = filters or VisitFilters()
        if filters.facility:
            df = df[df["facility"] == filters.facility]
        if filters.pediatric_only:
            df = df[df["age_group"].isin(["Newborn", "Neonate", "Paediatric"])]
        return df.reset_index(drop=True)

    def load_waiting_room_registry(self) -> pd.DataFrame:
        """Return all current registry rows for manual MRN selection."""

        return self.load_current_active_visits(VisitFilters())

    def save_waiting_room_registry(self, registry: pd.DataFrame) -> None:
        """Persist a changed synthetic registry."""

        registry.to_csv(self.paths["waiting_room"], index=False)

    def load_chart_context_by_mrn(self, mrn: str) -> ChartContext:
        """Load normalized chart source sections by synthetic MRN."""

        notes = pd.read_csv(self.paths["chart_notes"])
        notes = ensure_datetime(notes, ["contact_datetime", "updated_datetime"])
        registry = self.load_waiting_room_registry()
        patient_rows = registry[registry["mrn"].astype(str) == str(mrn)]
        demographics = {}
        if not patient_rows.empty:
            row = patient_rows.iloc[0].to_dict()
            demographics = {
                "synthetic_patient_name": row.get("synthetic_patient_name"),
                "age": row.get("age"),
                "age_group": row.get("age_group"),
                "sex": row.get("sex"),
                "facility": row.get("facility"),
                "triage_level": row.get("triage_level"),
                "presenting_complaint": row.get("presenting_complaint"),
                "current_stage": row.get("current_stage"),
            }
        patient_notes = notes[notes["mrn"].astype(str) == str(mrn)].copy()
        sections: dict[str, ChartSection] = {}
        for section_name, group in patient_notes.groupby("source_type"):
            group = group.sort_values("updated_datetime", ascending=False)
            text = "\n".join(group["note_text"].dropna().astype(str).head(4).tolist())
            freshness = group["updated_datetime"].max()
            sections[str(section_name)] = ChartSection(
                name=str(section_name),
                content=text,
                freshness=freshness.to_pydatetime() if pd.notna(freshness) else None,
                source_count=int(len(group)),
            )
        latest = patient_notes["updated_datetime"].max() if not patient_notes.empty else pd.NaT
        return ChartContext(
            mrn=str(mrn),
            mapped_source_field="PATIENT_CHART -> PAT_MRN_ID synthetic mapping",
            sections=sections,
            demographics=demographics,
            freshness=latest.to_pydatetime() if pd.notna(latest) else None,
        )

    def load_expanded_flow_events(self) -> pd.DataFrame:
        """Load synthetic expanded system events."""

        df = pd.read_csv(self.paths["expanded_events"])
        return ensure_datetime(df, ["event_datetime"])

    def load_beds_staffing_diagnostics(self) -> pd.DataFrame:
        """Load synthetic capacity snapshots."""

        df = pd.read_csv(self.paths["beds_staffing"])
        return ensure_datetime(df, ["snapshot_datetime"])

