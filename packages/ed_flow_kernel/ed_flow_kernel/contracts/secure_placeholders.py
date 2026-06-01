"""Contracts for secure operational feeds not present in the public prototype."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SecurePlaceholderContract(BaseModel):
    """A future internal feed needed for richer digital-twin behaviour."""

    name: str
    expected_grain: str
    owner_to_confirm: str = "AHS governed source owner"
    activation_status: str = "future secure internal feed"
    likely_phi_risk: str = "to assess"
    needed_for: list[str] = Field(default_factory=list)


def default_secure_placeholders() -> list[SecurePlaceholderContract]:
    """Return the expected internal feeds for Snowflake activation planning."""

    return [
        SecurePlaceholderContract(name="ADT bed board status", expected_grain="bed/unit status event", needed_for=["boarding", "bed-placement optimizer"]),
        SecurePlaceholderContract(name="staffing rosters", expected_grain="shift/person-role assignment", needed_for=["staffing sensitivity", "resource pools"]),
        SecurePlaceholderContract(name="diagnostic turnaround", expected_grain="order/result event", needed_for=["diagnostic constraints", "simulation calibration"]),
        SecurePlaceholderContract(name="consult queues", expected_grain="consult request/completion", needed_for=["consult delay", "service load"]),
        SecurePlaceholderContract(name="EMS offload events", expected_grain="arrival/handoff event", needed_for=["EMS process improvement"]),
    ]
