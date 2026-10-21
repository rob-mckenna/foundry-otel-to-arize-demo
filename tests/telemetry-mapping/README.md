# Telemetry mapping regression tests

Synthetic offline fixtures exercise the production mapper's native AppRequests
and AppDependencies compatibility, original identity/parent linkage, timing/status,
available model/correlation/token fields, and per-side OpenInference/inline I/O.
No real telemetry or live service calls are used.

Durable cross-batch AppGenAIContent precedence, deadlines and delivery safety tests
live in [`src/telemetry-pipeline/tests`](../../src/telemetry-pipeline/tests).
See the [component README](../../src/telemetry-pipeline/README.md) for settings and
the combined test command.
