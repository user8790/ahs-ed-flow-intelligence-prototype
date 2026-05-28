from __future__ import annotations

from ed_flow.ai_layer import MockModelClient
from ed_flow.chart_review import summarize_chart_context
from ed_flow.data_contracts import ChartContext, ChartSection


def test_chart_summary_handles_missing_sections() -> None:
    context = ChartContext(mrn="SYN-MRN-MISSING")

    summary = summarize_chart_context(context, MockModelClient())

    assert summary["active_problem_list"] == "No synthetic source data available for this section."
    assert "No source" in summary["source_list"]


def test_chart_summary_uses_available_sources() -> None:
    context = ChartContext(
        mrn="SYN-MRN-123",
        demographics={"triage_level": 3, "presenting_complaint": "Fever", "current_stage": "triaged_waiting"},
        sections={
            "ed_provider_notes": ChartSection(
                name="ed_provider_notes",
                content="Synthetic ED note: fever assessment only.",
                source_count=1,
            )
        },
    )

    summary = summarize_chart_context(context, MockModelClient())

    assert "Synthetic CTAS 3 patient with Fever" in summary["one_line_clinical_context"]
    assert "fever assessment" in summary["recent_ed_provider_note_highlights"]

