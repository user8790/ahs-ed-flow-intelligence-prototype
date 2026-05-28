"""Snowflake adapter and SQL templates for transfer readiness."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import pandas as pd

from ed_flow.config import AppConfig, DEFAULT_DATA_DIR
from ed_flow.data_contracts import SEMANTIC_VIEW_COLUMNS, SNOWFLAKE_SELECT_COLUMNS, VisitFilters


def build_ed_visits_sql(include_scheduled: bool = False, include_invalid_los: bool = False) -> str:
    """Build the constrained TB_ED_VISITS extraction SQL."""

    select_list = ",\n  ".join(SNOWFLAKE_SELECT_COLUMNS)
    filters = [
        "FIRST_CONTACT_DATETIME >= :start_datetime",
        "FIRST_CONTACT_DATETIME < :end_datetime",
    ]
    if not include_invalid_los:
        filters.insert(0, "INVALID_LOS_CALC_FLAG <> 'Y'")
    if not include_scheduled:
        filters.insert(1 if not include_invalid_los else 0, "COALESCE(SCHEDULED_ED_VISIT_FLAG, 'N') <> 'Y'")
    where_clause = "\n  AND ".join(filters)
    return f"""SELECT
  {select_list}
FROM TB_ED_VISITS
WHERE {where_clause};"""


def build_recent_ed_visits_sql() -> str:
    """SQL template for recent operational extract."""

    return build_ed_visits_sql()[:-1] + "\n  AND FIRST_CONTACT_DATETIME >= DATEADD(day, -14, CURRENT_TIMESTAMP());"


def build_active_visits_sql() -> str:
    """SQL template for active visits using the constrained timestamp fields."""

    return build_ed_visits_sql(include_invalid_los=True)[:-1] + """
  AND DISPOSITION_PERFORMANCE_REPORT = 'Active'
  AND DEPART_ED_DATETIME IS NULL;"""


def build_chart_context_sql(database: str, schema: str, mrn: str | None = None) -> dict[str, str]:
    """Build MRN-scoped SQL templates for all chart semantic views."""

    templates: dict[str, str] = {}
    for view_name, columns in SEMANTIC_VIEW_COLUMNS.items():
        select_list = ", ".join(columns)
        order_cols = [
            col
            for col in ["UPD_AUT_LOCAL_DTTM", "ENT_INST_LOCAL_DTTM", "CONTACT_DATE", "ORDERING_DATE", "RESULT_TIME", "ENTRY_DATE"]
            if col in columns
        ]
        order_expression = ", ".join(order_cols) if order_cols else "PAT_MRN_ID"
        templates[view_name] = (
            f"SELECT {select_list}\n"
            f"FROM {database}.{schema}.{view_name}\n"
            "WHERE PAT_MRN_ID = :mrn\n"
            f"ORDER BY {order_expression} DESC"
        )
        if mrn:
            templates[view_name] += f"\n-- Review bind value only in secure runtime: {mrn}"
    return templates


def _get_active_snowflake_session() -> Any | None:
    try:
        from snowflake.snowpark.context import get_active_session

        return get_active_session()
    except Exception:
        return None


@dataclass
class SnowflakeBackend:
    """Snowflake-first adapter with local fallback for development."""

    config: AppConfig
    fallback_to_local: bool = True

    def __post_init__(self) -> None:
        self.session = _get_active_snowflake_session()
        self._local = None
        if self.session is None and self.fallback_to_local:
            from ed_flow.local_backend import LocalBackend

            self._local = LocalBackend(DEFAULT_DATA_DIR)

    def _execute_to_pandas(self, query: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
        if self.session is None:
            raise RuntimeError("No active Snowflake session is available.")
        try:
            return self.session.sql(query, params=params).to_pandas()
        except TypeError:
            return self.session.sql(query).to_pandas()

    def load_ed_visits(self, filters: VisitFilters | None = None) -> pd.DataFrame:
        filters = filters or VisitFilters()
        if self.session is None and self._local is not None:
            return self._local.load_ed_visits(filters)
        query = build_ed_visits_sql(filters.include_scheduled, filters.include_invalid_los)
        params = {
            "start_datetime": filters.start_datetime,
            "end_datetime": filters.end_datetime,
        }
        df = self._execute_to_pandas(query, params)
        if filters.facility and "INSTITUTION_NAME" in df:
            df = df[df["INSTITUTION_NAME"] == filters.facility]
        if filters.pediatric_only and "PATIENT_AGE_GROUP" in df:
            df = df[df["PATIENT_AGE_GROUP"].isin(["Newborn", "Neonate", "Paediatric"])]
        return df.reset_index(drop=True)

    def load_recent_ed_visits(self, filters: VisitFilters | None = None) -> pd.DataFrame:
        if self.session is None and self._local is not None:
            return self._local.load_recent_ed_visits(filters)
        return self._execute_to_pandas(build_recent_ed_visits_sql())

    def load_current_active_visits(self, filters: VisitFilters | None = None) -> pd.DataFrame:
        if self.session is None and self._local is not None:
            return self._local.load_current_active_visits(filters)
        return self._execute_to_pandas(build_active_visits_sql())

    def load_waiting_room_registry(self) -> pd.DataFrame:
        if self.session is None and self._local is not None:
            return self._local.load_waiting_room_registry()
        return self.load_current_active_visits(VisitFilters())

    def save_waiting_room_registry(self, registry: pd.DataFrame) -> None:
        if self.session is None and self._local is not None:
            self._local.save_waiting_room_registry(registry)
            return
        raise NotImplementedError("Snowflake registry persistence requires governed target table approval.")

    def load_chart_context_by_mrn(self, mrn: str):
        if self.session is None and self._local is not None:
            return self._local.load_chart_context_by_mrn(mrn)
        templates = build_chart_context_sql(
            self.config.snowflake_database,
            self.config.snowflake_schema,
        )
        frames = {}
        for view_name, query in templates.items():
            frames[view_name] = self._execute_to_pandas(query, {"mrn": mrn})
        from ed_flow.chart_review import chart_context_from_semantic_frames

        return chart_context_from_semantic_frames(mrn, frames)


def fallback_connection_environment_notes() -> dict[str, str]:
    """Document env names for local Snowflake development."""

    return {
        "SNOWFLAKE_ACCOUNT": os.getenv("SNOWFLAKE_ACCOUNT", ""),
        "SNOWFLAKE_USER": os.getenv("SNOWFLAKE_USER", ""),
        "SNOWFLAKE_ROLE": os.getenv("SNOWFLAKE_ROLE", ""),
        "SNOWFLAKE_WAREHOUSE": os.getenv("SNOWFLAKE_WAREHOUSE", "WH_SMALL"),
        "SNOWFLAKE_DATABASE": os.getenv(
            "SNOWFLAKE_DATABASE",
            "DB_TEAM_STOLLERY_AND_ALBERTA_CHILDRENS_HOSPITAL_ANALYTICS",
        ),
        "SNOWFLAKE_SCHEMA": os.getenv("SNOWFLAKE_SCHEMA", "MSB_CLINICAL_GENETICS"),
    }
