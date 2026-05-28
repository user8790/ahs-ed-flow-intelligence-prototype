"""Controlled model-provider layer for summaries and explanations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ed_flow.config import AppConfig
from ed_flow.data_contracts import ChartContext


CHART_SUMMARY_SECTIONS = [
    "one_line_clinical_context",
    "recent_ed_provider_note_highlights",
    "active_problem_list",
    "relevant_medical_history",
    "recent_consult_referral_context",
    "imaging_highlights",
    "lab_result_comment_highlights",
    "open_questions_missing_information",
    "source_freshness",
    "source_list",
]


class ModelClient(ABC):
    """Interface for local, OpenAI, Snowflake-native, or no-op model calls."""

    @abstractmethod
    def summarize_chart(self, context: ChartContext) -> dict[str, str]:
        """Create a structured chart-review summary."""

    @abstractmethod
    def explain_scenario(self, scenario_table: Any) -> str:
        """Explain simulation output in operational terms."""


def _section_text(context: ChartContext, section: str) -> str:
    source = context.sections.get(section)
    if source is None or not source.content.strip():
        return "No synthetic source data available for this section."
    return source.content.strip()


class MockModelClient(ModelClient):
    """Deterministic local provider for PHI-free prototype use."""

    def summarize_chart(self, context: ChartContext) -> dict[str, str]:
        demographics = context.demographics or {}
        complaint = demographics.get("presenting_complaint", "No synthetic complaint recorded")
        triage = demographics.get("triage_level", "unknown")
        stage = demographics.get("current_stage", "unknown stage")
        source_names = sorted(context.sections)
        freshness = context.freshness.isoformat(timespec="minutes") if context.freshness else "No source freshness available"
        return {
            "one_line_clinical_context": f"Synthetic CTAS {triage} patient with {complaint}; current operational stage is {stage}.",
            "recent_ed_provider_note_highlights": _section_text(context, "ed_provider_notes"),
            "active_problem_list": _section_text(context, "problem_list"),
            "relevant_medical_history": _section_text(context, "medical_history"),
            "recent_consult_referral_context": "\n".join(
                [
                    _section_text(context, "consult_notes"),
                    _section_text(context, "referrals"),
                ]
            ).strip(),
            "imaging_highlights": _section_text(context, "imaging"),
            "lab_result_comment_highlights": _section_text(context, "labs"),
            "open_questions_missing_information": (
                "Confirm current vitals, reassessment notes, pending diagnostics, and disposition plan in the source chart. "
                "This mock summary does not infer undocumented findings."
            ),
            "source_freshness": freshness,
            "source_list": ", ".join(source_names) if source_names else "No source sections available.",
        }

    def explain_scenario(self, scenario_table: Any) -> str:
        try:
            rows = len(scenario_table)
        except Exception:
            rows = 0
        return (
            f"Mock interpretation based on {rows} scenario rows: compare the uncertainty intervals, then focus on "
            "interventions that move the current bottleneck without creating a larger downstream queue."
        )


class OpenAIModelClient(ModelClient):
    """Optional OpenAI provider. Inactive unless configured and dependency is present."""

    def __init__(self, config: AppConfig):
        self.config = config

    def summarize_chart(self, context: ChartContext) -> dict[str, str]:
        if not self.config.openai_api_key:
            return MockModelClient().summarize_chart(context)
        try:
            from openai import OpenAI
        except Exception:
            return MockModelClient().summarize_chart(context)
        client = OpenAI(api_key=self.config.openai_api_key)
        prompt = (
            "Summarize the following synthetic chart context into the required section headings. "
            "Do not invent facts. If a section has no source data, say so.\n\n"
            f"MRN: {context.mrn}\n"
            f"Demographics: {context.demographics}\n"
            f"Sections: {context.sections}"
        )
        response = client.responses.create(
            model=self.config.openai_model,
            input=prompt,
        )
        text = getattr(response, "output_text", "")
        summary = MockModelClient().summarize_chart(context)
        summary["one_line_clinical_context"] = text[:900] if text else summary["one_line_clinical_context"]
        return summary

    def explain_scenario(self, scenario_table: Any) -> str:
        if not self.config.openai_api_key:
            return MockModelClient().explain_scenario(scenario_table)
        return MockModelClient().explain_scenario(scenario_table)


class SnowflakeModelClient(ModelClient):
    """Placeholder for Cortex/Snowflake-native governed model calls."""

    def summarize_chart(self, context: ChartContext) -> dict[str, str]:
        summary = MockModelClient().summarize_chart(context)
        summary["source_list"] += " Snowflake-native model call placeholder was not invoked locally."
        return summary

    def explain_scenario(self, scenario_table: Any) -> str:
        return (
            "Snowflake-native model explanation placeholder: future implementation should call approved internal "
            "model endpoints and persist prompts/responses to the audit design."
        )


class NoModelClient(MockModelClient):
    """Explicit no-model option that returns deterministic template text."""


def get_model_client(config: AppConfig) -> ModelClient:
    """Return provider selected by config."""

    if config.model_provider == "openai":
        return OpenAIModelClient(config)
    if config.model_provider == "snowflake":
        return SnowflakeModelClient()
    return NoModelClient() if config.model_provider == "none" else MockModelClient()
