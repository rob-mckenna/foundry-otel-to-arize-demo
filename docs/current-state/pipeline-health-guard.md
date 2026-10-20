# Pipeline-health export guard (#153)

**CURRENT-STATE implementation; synthetic offline validation only for this change.
Not deployed or live-validated.** This guard protects the existing Application
Insights → Log Analytics → Event Hub → Function → Arize pipeline. It does not
introduce a direct-OTLP bypass or prove whole-trace completeness.

## Exact identity configuration

Both Function paths use the same `SourcePolicy`:

| Setting | Compatibility default | Match |
| --- | --- | --- |
| `PIPELINE_EXCLUDED_SERVICE_NAMES` | `[]` | Exact, case-sensitive source `AppRoleName` / `cloud_RoleName` |
| `PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS` | `[]` | Exact, case-insensitive source `_ResourceId` |

Values must be JSON arrays of nonempty strings, with no surrounding whitespace
inside a string. Invalid JSON, null/scalar/object values, non-string entries,
empty entries and padded entries fail configuration explicitly before processing.
Empty arrays preserve prior export selection. Missing/empty source roles do not
match a service exclusion. Native and normalized role aliases must agree, including
when one is null; a disagreement or wrong identity type is rejected per-record
without selecting an alias or poisoning valid neighboring records.

Configure the actual Function role as
`PIPELINE_EXCLUDED_SERVICE_NAMES=["fotoa-demo-func-eastus2"]`. Infra supplies the
separate health component's full ARM ID in the component array after establishing
that resource under separately approved change control. Do **not** exclude the old
shared agent component: genuine agent telemetry still originates there.

These are source identities, not operation names, prefixes, mapped resource
fallbacks, or trace-wide classifications. Even explicitly excluding
`telemetry-pipeline-function` does not reject a missing-role row merely because
the mapper supplies that fallback. Genuine agent roots and LLM, tool, retriever,
HTTP/request and dependency children remain eligible, including names resembling
the Function's. Existing mapping, identifiers, tokens, inline content precedence
and content joins are unchanged for eligible records.

## Legacy, admission and backlog behavior

- Legacy batch export checks the policy before mapping/export. Matched rows are
  counted in `BatchResult.skipped` with `excluded:service_identity` or
  `excluded:component_identity`. Only retained valid spans reach the batch exporter;
  exclusions log fixed reason codes, not payloads.
- Durable admission keeps the existing workspace/component source allowlist.
  Allowed excluded originals/content create an `excluded` ledger terminal using
  the same trace/span and source/destination namespace. Excluded foreign sources
  cannot create entries in that namespace; they are skipped, not admitted, without
  blocking valid neighbors. Other disallowed originals retain admission failure.
- The timer applies the policy to stored originals in `pending` and `retry` **before**
  readiness, `allow_send`, freezing or acquiring a send claim. This covers queued
  pre-cutover originals even if no duplicate arrives. `retry` is the existing
  explicit HTTP-429/nonacceptance state, not an ambiguous network outcome.
  Indexed scans remain bounded and due-time based: a pending join or future retry
  may wait until its existing scan time to be retired, but cannot send first.
- A stored original is authoritative. Conflicting pending duplicate originals
  retain `original_identity_conflict`; excluded content cannot retire a legitimate
  stored original or attach content to it. Content-only records never create spans.
- `excluded` is **not** an acknowledgment of export. It stores only state, fixed
  reason, exclusion time and expiry; original content, candidates and frozen wire
  bytes are removed atomically under the existing ETag compare-and-swap.
  Duplicate originals/content cannot reopen it or extend its expiry.
- Retention reuses the existing **48-hour** acknowledgment horizon. Tombstones
  receive an expiry index tag and are conditionally deleted by the bounded timer
  after expiry. This bounds deduplication; it is not eternal replay protection.
  There is no blanket ledger deletion or replay.
- Existing `acknowledged`, active `sending`, `ambiguous` and `rejected` history is
  not reclassified or replayed. Expired send claims still become `ambiguous` through
  the existing recovery path. An exclusion CAS that loses to a concurrent claim
  must reread and preserve that claim. Frozen-payload integrity and uncertain-send
  quarantine remain intact.

Genuine GenAI originals retain the **300-second** first-admission deadline,
input/output completeness check and `deadline_missing` fallback. Duplicates and
content do not reset that deadline. Ordinary non-GenAI spans remain immediately
ready; exclusion is not LLM-only filtering.

## Validation and limitations

Synthetic tests cover operation-independent service rejection, native/normalized
mixed batches and alias conflicts, missing/fallback roles, exact/case behavior,
component matching, genuine non-LLM children, cross-batch/content-first admission,
queued pending/retry originals, duplicate/content suppression and tombstone expiry,
unchanged good-record deadlines, and delivery quarantine/claim races. Existing
mapping/export suites validate retained identifier, token and content behavior.
No real telemetry payloads or live settings were inspected.

Executed from the assigned worktree with
`$env:PYTHONPATH = "$PWD\src\telemetry-pipeline"`:

```powershell
python -m pytest src\telemetry-pipeline\tests --ignore=src\telemetry-pipeline\tests\test_durable_infra.py tests\telemetry-mapping tests\export -q
```

Result: **314 passed** (2026-10-20). Infrastructure tests are independently owned
by Infra. `git diff --check` passed. A process-local negative control replaced
`SourcePolicy.exclusion_reason` with a no-op and ran
`test_mixed_native_normalized_aliases_and_component` plus both parameters of
`test_guard_removes_pre_cutover_unsent_original_before_readiness_or_send_budget`:
**3 failed as expected**, demonstrating sensitivity to a missing guard. This
control changed no source files.

The guard cannot retract spans already delivered to Arize, infer a missing role,
or recover never-admitted events. Finite Function retry/checkpoint limitations
remain. Source isolation is the primary remedy: host, worker and SDK health must
use the dedicated **non-exported** health LAW, with no diagnostic/indirect route
back to the exported agent LAW or Event Hub. See Infra's
[cutover runbook](pipeline-health-cutover.md) for approval, routing and rollback
constraints. Do not reset checkpoints, namespaces, ledger entries or quarantine
as part of cutover; do not roll back health into an actively exported shared LAW.
