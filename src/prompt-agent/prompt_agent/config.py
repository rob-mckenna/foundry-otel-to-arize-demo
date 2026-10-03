"""Configuration loading for the Foundry Prompt Agent.

Hard rule (see /.github/copilot-instructions.md §8): never hardcode secrets,
connection strings, or API keys in this repo. All configuration is sourced
from environment variables. In a real deployment those environment variables
would themselves be populated from Azure Key Vault references (e.g. via App
Service / Function App "Key Vault reference" app settings) — this module
never talks to Key Vault directly, it only reads whatever the process
environment hands it.

For local development without Azure resources provisioned yet, every value
has a clearly-fake placeholder default so the scaffold runs out of the box.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    """Read an environment variable, falling back to a placeholder default.

    Placeholder defaults are intentionally obviously-fake (never real
    endpoints/keys) so nobody mistakes them for working credentials.
    """
    return os.environ.get(name, default)


@dataclass(frozen=True)
class PromptAgentConfig:
    """Runtime configuration for the Foundry Prompt Agent.

    All fields are sourced from environment variables — see the matching
    `FOUNDRY_*` / `OTEL_*` names below. None of these defaults are real
    endpoints, deployment names, or keys.
    """

    foundry_endpoint: str
    foundry_deployment_name: str
    foundry_api_key: str
    service_name: str
    service_version: str
    deployment_environment: str
    retry_max_attempts: int
    retry_initial_backoff_seconds: float
    retry_backoff_multiplier: float

    @property
    def has_placeholder_credentials(self) -> bool:
        """True when the agent is running against placeholder/synthetic config.

        Used to decide whether to use the real Foundry SDK call path or the
        stubbed/mocked call path (see prompt_agent/agent.py).
        """
        return self.foundry_api_key in ("", "REPLACE_ME_SYNTHETIC_KEY") or self.foundry_endpoint.startswith(
            "https://synthetic-placeholder"
        )


def load_config() -> PromptAgentConfig:
    """Load configuration from environment variables.

    Environment variables (all optional for local/demo use — defaults are
    synthetic placeholders, never real Foundry resources):
      - FOUNDRY_ENDPOINT
      - FOUNDRY_DEPLOYMENT_NAME
      - FOUNDRY_API_KEY           (sourced from Key Vault reference in real deployments)
      - OTEL_SERVICE_NAME
      - OTEL_SERVICE_VERSION
      - DEPLOYMENT_ENVIRONMENT
      - RETRY_MAX_ATTEMPTS               (default 3)
      - RETRY_INITIAL_BACKOFF_SECONDS    (default 0.1)
      - RETRY_BACKOFF_MULTIPLIER         (default 2.0)
    """
    return PromptAgentConfig(
        foundry_endpoint=_env("FOUNDRY_ENDPOINT", "https://synthetic-placeholder.foundry.azure.com"),
        foundry_deployment_name=_env("FOUNDRY_DEPLOYMENT_NAME", "synthetic-gpt-demo"),
        foundry_api_key=_env("FOUNDRY_API_KEY", "REPLACE_ME_SYNTHETIC_KEY"),
        service_name=_env("OTEL_SERVICE_NAME", "foundry-prompt-agent"),
        service_version=_env("OTEL_SERVICE_VERSION", "0.1.0"),
        deployment_environment=_env("DEPLOYMENT_ENVIRONMENT", "dev"),
        retry_max_attempts=int(_env("RETRY_MAX_ATTEMPTS", "3")),
        retry_initial_backoff_seconds=float(_env("RETRY_INITIAL_BACKOFF_SECONDS", "0.1")),
        retry_backoff_multiplier=float(_env("RETRY_BACKOFF_MULTIPLIER", "2.0")),
    )
