"""Model client interface for the Foundry Prompt Agent.

This module defines the boundary between the agent's request/response flow
and the actual model backend. In a fully provisioned environment,
`FoundryModelClient` would call the real Microsoft Foundry Prompt Agent SDK.
Since this sandbox has no live Foundry project/credentials provisioned yet
(see Infra's #15/#16/#18), `FoundryModelClient` falls back to a deterministic
stub so the rest of the pipeline (and its telemetry) can be built, run, and
tested end-to-end without live Azure resources.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from prompt_agent.config import PromptAgentConfig


@dataclass(frozen=True)
class ModelResponse:
    """Result of a single model invocation.

    `prompt_tokens`/`completion_tokens`/`total_tokens` mirror the token-usage
    fields the Foundry model API returns, so downstream OpenInference
    attribute mapping (#28) has real numbers to attach, not estimates.
    """

    text: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class ModelClient(Protocol):
    """Protocol every model backend (real or stub) must satisfy."""

    def complete(self, prompt: str) -> ModelResponse:
        ...


def _estimate_tokens(text: str) -> int:
    """Very rough whitespace-based token estimate for the stub backend only.

    The real Foundry/OpenAI-compatible API returns authoritative token
    counts in its response payload; this helper exists solely so the stub
    backend can produce plausible, internally-consistent numbers when no
    real model call is available. Never used once a real model client is
    wired in (see FoundryModelClient docstring).
    """
    return max(1, len(text.split()))


class StubFoundryModelClient:
    """Deterministic stand-in for the real Foundry Prompt Agent SDK call.

    # STUB: replace with real Foundry Prompt Agent SDK call.
    #
    # Once Infra provisions a live Foundry project/deployment (#15/#16) and
    # the real connection details are available, swap this class out for one
    # that calls the actual `azure-ai-projects` / Foundry Prompt Agent SDK
    # chat-completion API. The `ModelClient` protocol above is the seam:
    # anything satisfying `complete(prompt) -> ModelResponse` can be dropped
    # in without touching `agent.py` or the instrumentation layer (#27/#28).
    #
    # This stub returns canned, keyword-matched synthetic answers so the
    # demo scenarios in `synthetic/scenarios.py` produce coherent, stable
    # responses without any network/model dependency.
    """

    def __init__(self, config: PromptAgentConfig) -> None:
        self._config = config

    def complete(self, prompt: str) -> ModelResponse:
        text = self._synthetic_answer(prompt)
        return ModelResponse(
            text=text,
            model_name=self._config.foundry_deployment_name,
            prompt_tokens=_estimate_tokens(prompt),
            completion_tokens=_estimate_tokens(text),
        )

    @staticmethod
    def _synthetic_answer(prompt: str) -> str:
        # Only match keywords against the original user question, not any
        # appended synthetic tool-lookup context (which may itself contain
        # overlapping keywords, e.g. "deductible" appearing in plan details
        # regardless of what the member actually asked).
        user_question = prompt.split("\n\n[Synthetic plan lookup result:", 1)[0]
        lowered = user_question.lower()
        if "deductible" in lowered:
            return (
                "Your synthetic deductible under Acme Synthetic PPO is $500 "
                "individual / $1,000 family for this benefit year."
            )
        if "copay" in lowered or "co-pay" in lowered:
            return "Your synthetic primary care copay is $25 per visit under Acme Synthetic PPO."
        if "member id" in lowered or "member number" in lowered:
            return "Your synthetic member ID on file is SYN-00042."
        if "in-network" in lowered or "network" in lowered:
            return (
                "Acme Synthetic PPO covers in-network primary care visits at 100% "
                "after your deductible is met."
            )
        if "claim" in lowered:
            return "Your most recent synthetic claim (CLM-SYN-9001) was processed and paid in full."
        return (
            "This is a synthetic member-services response for demo purposes only — "
            "no real benefits data is represented."
        )
