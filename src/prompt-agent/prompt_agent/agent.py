"""Core prompt/response flow for the Foundry Prompt Agent.

This module implements the primary request/response pipeline described in
#25: accept a user prompt, optionally resolve it via a small lookup "tool"
call, invoke the model, and return a response.

OpenTelemetry span instrumentation is added around these calls in #27/#28;
this module intentionally has no tracing code yet so each issue's diff stays
reviewable on its own.
"""
from __future__ import annotations

from dataclasses import dataclass

from prompt_agent.config import PromptAgentConfig, load_config
from prompt_agent.model_client import ModelClient, ModelResponse, StubFoundryModelClient

# Synthetic plan directory used by the `lookup_plan_details` tool call below.
# Entirely fabricated — see synthetic/README.md.
_SYNTHETIC_PLAN_DIRECTORY: dict[str, str] = {
    "acme synthetic ppo": "Acme Synthetic PPO — $500/$1,000 deductible, $25 PCP copay, in-network only after deductible.",
    "acme synthetic hmo": "Acme Synthetic HMO — requires in-network PCP referral, $15 PCP copay, no out-of-network coverage.",
}


def lookup_plan_details(plan_name: str) -> str:
    """Synthetic "tool" call: looks up fabricated plan details by name.

    Exists so the agent has at least one tool/function call in its request
    path (in addition to the model call) for #27's span instrumentation to
    wrap. Entirely synthetic data — never a real plan lookup.
    """
    return _SYNTHETIC_PLAN_DIRECTORY.get(
        plan_name.strip().lower(),
        f"No synthetic plan details on file for '{plan_name}'.",
    )


@dataclass(frozen=True)
class AgentResult:
    """Full result of one `PromptAgent.invoke()` call."""

    prompt: str
    response: ModelResponse
    tool_output: str | None


class PromptAgent:
    """Primary request/response entry point for the Foundry Prompt Agent."""

    def __init__(self, config: PromptAgentConfig | None = None, model_client: ModelClient | None = None) -> None:
        self._config = config or load_config()
        # Real-SDK wiring lives behind the ModelClient protocol — swap this
        # default for a real Foundry-backed client once credentials exist.
        self._model_client = model_client or StubFoundryModelClient(self._config)

    def invoke(self, prompt: str, plan_name: str | None = None) -> AgentResult:
        """Run one request through the core prompt/response flow.

        If `plan_name` is given, the `lookup_plan_details` tool call runs
        first and its output is folded into the prompt sent to the model —
        a minimal "tool use" path for #27 to instrument.
        """
        tool_output: str | None = None
        effective_prompt = prompt
        if plan_name:
            tool_output = lookup_plan_details(plan_name)
            effective_prompt = f"{prompt}\n\n[Synthetic plan lookup result: {tool_output}]"

        response = self._model_client.complete(effective_prompt)
        return AgentResult(prompt=prompt, response=response, tool_output=tool_output)
