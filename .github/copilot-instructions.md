# Contribution rules

## Scope and architecture

This is a synthetic-data-only technical preview, not a production landing zone.
Support one path: an exact existing versioned Foundry Agent invocation → native
agent Application Insights / Log Analytics → Event Hub → durable Azure Function
→ Arize OTLP. Function health uses a separate, non-exported workspace.

Keep implementation under `src` and `infra`; keep the README and the three
`docs/current-state` pages accurate. The caller is a real managed-identity
Responses client, not a simulator, agent registrar or telemetry exporter.
The Function admits, validates, joins content to its original span, maps and
delivers; it never calls a model. Do not restore legacy batch/console paths,
runtime mode selectors, incident tooling or fresh-foundation modules.

Distinguish implemented source, offline tests and previously observed cloud
behavior. New package/live parity, fresh/repeat deployment and private Agent
runtime acceptance remain unverified. The source guard is not deployed proof.
Never claim whole-trace reconstruction, full resource parity, lossless admission
or exactly-once delivery. Direct Agent-to-Arize OTLP is **CONCEPTUAL — NOT
IMPLEMENTED**, not a supported path; architectural expansion needs explicit
review and approval before implementation. Conceptual diagrams must be dashed
and explicitly labeled, never styled as validated architecture.

## Data and credentials

- Use fabricated prompts, responses, fixtures, screenshots and examples only.
  No real patient/member/claims data, PII/PHI or customer-identifying content,
  including in issues, logs and commit history.
- Never read `.env` or credential files. Use placeholder examples and documented
  schemas. Never commit secrets, raw telemetry, connection strings, tokens,
  local configuration or live receipts.
- Store secrets in Azure Key Vault; prefer managed identity for Azure access.
  Document any non-MI exception (Arize API-key authentication is one).
- Keep logs content-free and bounded. Do not print SDK/parser exceptions,
  request bodies, full configuration, credentials or raw records.
- Preserve private network posture, scoped permissions and fail-closed behavior.
  Do not add public access, shared-key auth, developer credential fallbacks,
  broad RBAC or remote-build/SCM workarounds.

## Approval and workspace boundary

Offline checks grant no live authority. Azure reads/writes, deployment/what-if,
resource or role changes, registration, package publication, trigger activation,
replay, Arize access and model calls each need explicit scoped approval.
The caller defaults to refusal without `--dry-run` or separately approved
`--allow-live`; preserve exact version binding, bounded cost/time, no automatic
model retry and once-only repository-local receipt custody. Never retry an
uncertain invocation by changing its UUID. Preparation leaves both Function
triggers disabled; it is not activation or readiness.

Operate only within the assigned repository/worktree. Do not inspect host/home
or sibling-repository files or hunt for another environment. Use repository-local
virtual environments, caches, compiler downloads and build output. Do not
reset/stash/clean/switch a shared checkout or remove another worktree's files.

## Telemetry correctness

Preserve valid trace IDs, span IDs, parent IDs, source correlation, model and
prompt/completion/total usage wherever supplied and supported. Never invent
missing source values, calculate a source total, or substitute a caller trace ID
for a native Agent trace ID. Document mapping gaps explicitly.

Retain exact workspace/component/destination admission, per-span joins, content
precedence, finite deadlines/bounds, durable ETag ownership, frozen export bytes,
strict acknowledgment and quarantine of ambiguous sends. Content-only records
must not create spans. Keep health isolation and source/backlog guards intact.
Do not weaken delivery safeguards to make a test or demo pass.

## Changes and validation

Use Python for both components and Bicep for existing-resource attachment only.
Keep changes focused; update related documentation and tests in the same change.
Telemetry changes require component, root mapping and export tests. Infra or
package changes require offline preparation, standalone Bicep compilation and
all infra/package tests, including compiled cases; missing compiler is a blocker,
not a successful skipped validation.

Follow `CONTRIBUTING.md` and `.github/workflows/ci.yml`. Report exact commands,
results, skips and dependency-install limitations. Offline mocks and package
hash receipts are not live compatibility or deployment proof.
Preserve the full `.github/pull_request_template.md` when preparing a PR, report
actual evidence and limitations, and obtain separate approval before push,
PR creation or merge.
