"""Chart-review context normalization and mock summarization workflow."""

from __future__ import annotations

import pandas as pd

from ed_flow.ai_layer import ModelClient
from ed_flow.data_contracts import ChartContext, ChartSection


SECTION_MAP = {
    "SV_EDPROVIDER_NOTES": ("ed_provider_notes", "NOTE_TEXT"),
    "SV_ENC_NOTES": ("encounter_notes", "NOTE_TEXT"),
    "SV_CONSULT_NOTES": ("consult_notes", "NOTE_TEXT"),
    "SV_ADMISSION_HP_NOTES": ("admission_hp_notes", "FULL_NOTE"),
    "SV_IMAGING_NOTES": ("imaging", "NARRATIVE"),
    "SV_LAB_REPORTS": ("labs", "RESULTS_COMP_CMT"),
    "SV_PROBLEM_LIST": ("problem_list", "DESCRIPTION"),
    "SV_MEDICAL_HISTORY": ("medical_history", "COMMENTS"),
    "SV_REFERRALS": ("referrals", "REASON_FOR_REFERRAL"),
}


def chart_context_from_semantic_frames(mrn: str, frames: dict[str, pd.DataFrame]) -> ChartContext:
    """Normalize Snowflake semantic view result frames into ChartContext."""

    sections: dict[str, ChartSection] = {}
    latest = pd.NaT
    for view_name, frame in frames.items():
        if frame is None or frame.empty or view_name not in SECTION_MAP:
            continue
        section_name, text_col = SECTION_MAP[view_name]
        column = text_col if text_col in frame.columns else next((c for c in frame.columns if "TEXT" in c or "NOTE" in c), None)
        if not column:
            continue
        text = "\n".join(frame[column].dropna().astype(str).head(5).tolist())
        freshness_cols = [
            col
            for col in ["UPD_AUT_LOCAL_DTTM", "ENT_INST_LOCAL_DTTM", "CONTACT_DATE", "ORDERING_DATE", "RESULT_TIME", "ENTRY_DATE"]
            if col in frame.columns
        ]
        freshness = pd.NaT
        if freshness_cols:
            freshness = pd.to_datetime(frame[freshness_cols].stack(), errors="coerce").max()
            latest = max(latest, freshness) if pd.notna(latest) and pd.notna(freshness) else freshness
        sections[section_name] = ChartSection(
            name=section_name,
            content=text,
            freshness=freshness.to_pydatetime() if pd.notna(freshness) else None,
            source_count=int(len(frame)),
        )
    return ChartContext(
        mrn=mrn,
        mapped_source_field="PATIENT_CHART to PAT_MRN_ID mapping requires validation",
        sections=sections,
        freshness=latest.to_pydatetime() if pd.notna(latest) else None,
    )


def summarize_chart_context(context: ChartContext, model_client: ModelClient) -> dict[str, str]:
    """Summarize chart context through the configured model interface."""

    return model_client.summarize_chart(context)


def empty_summary() -> dict[str, str]:
    """Return the required summary shape when there are no sources."""

    missing = "No synthetic source data available for this section."
    return {
        "one_line_clinical_context": missing,
        "recent_ed_provider_note_highlights": missing,
        "active_problem_list": missing,
        "relevant_medical_history": missing,
        "recent_consult_referral_context": missing,
        "imaging_highlights": missing,
        "lab_result_comment_highlights": missing,
        "open_questions_missing_information": missing,
        "source_freshness": "No source freshness available",
        "source_list": "No source sections available",
    }

