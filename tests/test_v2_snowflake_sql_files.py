from __future__ import annotations

from ed_flow_intelligence.snowflake_sql import available_sql_templates, load_sql_template


def test_v2_snowflake_sql_files_are_available() -> None:
    templates = set(available_sql_templates())
    expected = {
        "open_data_ddl.sql",
        "open_data_tasks.sql",
        "tb_ed_visits_core.sql",
        "tb_ed_visits_feature_views.sql",
        "semantic_view_queries.sql",
        "secure_internal_placeholders.sql",
        "lineage_and_refresh_tables.sql",
        "v_ed_visits_with_open_context.sql",
    }
    assert expected.issubset(templates)


def test_tb_ed_visits_core_sql_preserves_business_rules() -> None:
    sql = load_sql_template("tb_ed_visits_core.sql")
    assert "INVALID_LOS_CALC_FLAG <> 'Y'" in sql
    assert "COALESCE(SCHEDULED_ED_VISIT_FLAG, 'N') <> 'Y'" in sql
    assert "FIRST_CONTACT_DATETIME" in sql
    assert "ROW_CREATE_DATETIME" not in sql.split("SELECT", 1)[1].split("FROM", 1)[0]


def test_hybrid_sql_joins_open_context_without_patient_identifiers() -> None:
    sql = load_sql_template("v_ed_visits_with_open_context.sql")
    assert "HYBRID_OPEN_INTERNAL_READY" in sql
    assert "OPEN_DATA.AHS_ED_WAIT_TIMES" in sql
    assert "PATIENT_CHART" not in sql
    assert "PATIENT_PHN" not in sql
