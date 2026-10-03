"""Entry point for the Foundry Prompt Agent scaffold.

This module is intentionally thin: it loads configuration and returns a
placeholder "hello agent" response. Business logic (the real prompt/response
flow) is added in #25.
"""
from __future__ import annotations

from prompt_agent.config import load_config


def hello_agent() -> str:
    """Return a placeholder response proving the scaffold runs end-to-end.

    No business logic / model call yet — see #25 for the real prompt/response
    flow.
    """
    config = load_config()
    mode = "SYNTHETIC/PLACEHOLDER" if config.has_placeholder_credentials else "CONFIGURED"
    return (
        f"Hello from Foundry Prompt Agent '{config.service_name}' "
        f"v{config.service_version} ({config.deployment_environment}) — "
        f"deployment='{config.foundry_deployment_name}' mode={mode}."
    )


def main() -> int:
    print(hello_agent())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
