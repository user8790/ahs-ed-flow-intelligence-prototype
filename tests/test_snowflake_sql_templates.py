from __future__ import annotations

from ed_flow.snowflake_backend import build_active_visits_sql, build_chart_context_sql, build_ed_visits_sql


def test_snowflake_sql_templates_contain_expected_columns_and_filters() -> None:
    sql = build_ed_visits_sql()

    assert "DATA_RECORD_ID" in sql
    assert "INSTITUTION_NAME" in sql
    assert "ED_LOS_HRS" in sql
    assert "FROM TB_ED_VISITS" in sql
    assert "INVALID_LOS_CALC_FLAG <> 'Y'" in sql
    assert "COALESCE(SCHEDULED_ED_VISIT_FLAG, 'N') <> 'Y'" in sql
    assert "FIRST_CONTACT_DATETIME >= :start_datetime" in sql
    assert "ROW_CREATE_DATETIME" not in sql


def test_active_visit_sql_contains_active_logic() -> None:
    sql = build_active_visits_sql()

    assert "DISPOSITION_PERFORMANCE_REPORT = 'Active'" in sql
    assert "DEPART_ED_DATETIME IS NULL" in sql


def test_chart_review_templates_reference_semantic_views() -> None:
    templates = build_chart_context_sql("DB", "SCHEMA")

    assert "SV_EDPROVIDER_NOTES" in templates
    assert "SV_LAB_REPORTS" in templates
    assert all("PAT_MRN_ID = :mrn" in sql for sql in templates.values())
    assert "DB.SCHEMA.SV_REFERRALS" in templates["SV_REFERRALS"]

