"""Synthetic member-services / benefits-lookup scenario fixtures.

**Policy reminder:** every scenario here is entirely fabricated. Member IDs
use the `SYN-` prefix, plan names are obviously fictional ("Acme Synthetic
PPO"), and no field resembles a real insurer's real ID format, plan name, or
customer data. See `synthetic/README.md`.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    """A single synthetic member-services demo scenario."""

    scenario_id: str
    synthetic_member_id: str
    synthetic_plan_name: str
    prompt: str
    synthetic: bool = True


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        scenario_id="benefits-deductible-lookup",
        synthetic_member_id="SYN-00042",
        synthetic_plan_name="Acme Synthetic PPO",
        prompt="What is my synthetic deductible under Acme Synthetic PPO?",
    ),
    Scenario(
        scenario_id="benefits-copay-lookup",
        synthetic_member_id="SYN-00077",
        synthetic_plan_name="Acme Synthetic PPO",
        prompt="What is my copay for a primary care visit on Acme Synthetic PPO?",
    ),
    Scenario(
        scenario_id="member-id-confirmation",
        synthetic_member_id="SYN-00042",
        synthetic_plan_name="Acme Synthetic PPO",
        prompt="Can you confirm the member ID you have on file for me?",
    ),
    Scenario(
        scenario_id="network-coverage-lookup",
        synthetic_member_id="SYN-00118",
        synthetic_plan_name="Acme Synthetic HMO",
        prompt="Is my primary care doctor in-network under Acme Synthetic HMO?",
    ),
    Scenario(
        scenario_id="claim-status-lookup",
        synthetic_member_id="SYN-00077",
        synthetic_plan_name="Acme Synthetic PPO",
        prompt="What is the status of my most recent synthetic claim?",
    ),
)
