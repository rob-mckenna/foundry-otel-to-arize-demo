"""Entry point for the Foundry Prompt Agent.

Running with no arguments prints the placeholder "hello agent" line (kept
for #24's acceptance criteria). Pass `--scenarios` to run all synthetic
member-services scenarios from #25 end-to-end and print each prompt/response
pair. The OpenTelemetry SDK (#26) is bootstrapped once at startup regardless
of mode, so every run emits at least a startup span.
"""
from __future__ import annotations

import argparse

from prompt_agent.agent import PromptAgent
from prompt_agent.config import load_config
from prompt_agent.telemetry import configure_tracing, get_tracer, shutdown_tracing

try:  # synthetic/ lives at the project root, alongside prompt_agent/
    from synthetic.scenarios import SCENARIOS
except ImportError:  # pragma: no cover - fallback when run outside the repo layout
    SCENARIOS = ()


def hello_agent() -> str:
    """Return a placeholder response proving the scaffold runs end-to-end."""
    config = load_config()
    mode = "SYNTHETIC/PLACEHOLDER" if config.has_placeholder_credentials else "CONFIGURED"
    return (
        f"Hello from Foundry Prompt Agent '{config.service_name}' "
        f"v{config.service_version} ({config.deployment_environment}) — "
        f"deployment='{config.foundry_deployment_name}' mode={mode}."
    )


def run_scenarios() -> int:
    """Run every synthetic member-services scenario and print the result.

    All prompts/responses here are synthetic (see synthetic/scenarios.py and
    synthetic/README.md) — never real member/benefits data. Each scenario is
    treated as an independent request, so each gets its own freshly
    generated correlation ID (#29) — printed alongside the result so the
    correlation ID -> trace mapping is visible without needing a trace
    backend.
    """
    agent = PromptAgent()
    for scenario in SCENARIOS:
        result = agent.invoke(scenario.prompt, plan_name=scenario.synthetic_plan_name)
        print(f"--- scenario: {scenario.scenario_id} (synthetic_member_id={scenario.synthetic_member_id}) ---")
        print(f"correlation_id: {result.correlation_id}")
        print(f"prompt:    {result.prompt}")
        if result.tool_output:
            print(f"tool_out:  {result.tool_output}")
        print(f"response:  {result.response.text}")
        print(
            f"tokens:    prompt={result.response.prompt_tokens} "
            f"completion={result.response.completion_tokens} total={result.response.total_tokens}"
        )
        print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Foundry Prompt Agent (demo)")
    parser.add_argument(
        "--scenarios",
        action="store_true",
        help="Run all synthetic member-services demo scenarios instead of the placeholder hello.",
    )
    args = parser.parse_args()

    configure_tracing()
    tracer = get_tracer(__name__)
    try:
        # Manual startup span — proves the SDK/exporter pipeline is wired up
        # end-to-end (#26's validation step), independent of the model/tool
        # call spans added in #27.
        with tracer.start_as_current_span("prompt_agent.startup"):
            if args.scenarios:
                return run_scenarios()
            print(hello_agent())
            return 0
    finally:
        # Flush-on-shutdown so spans are not dropped on process exit.
        shutdown_tracing()


if __name__ == "__main__":
    raise SystemExit(main())
