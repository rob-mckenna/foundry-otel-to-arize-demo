# Issue 148: approved retained-network execution attempt

**STOPPED BEFORE MUTATION — policy applicability unresolved.**
Execution preflight: 2026-10-20 04:26–04:33 UTC. This is management-plane
metadata evidence, not runtime/model/content validation or retirement completion.

## Definitive continuation outcome and lease release

The narrowly resumed review ended at **2026-10-20T04:49:29Z**:
**DEFINITIVE TECHNICAL STOP; RELEASE148LEASE.** No further Azure operations
will be performed by this executor. Issue #148 and PR #152 remain open.
Both parent DELETE submission counts remain **zero**, including the earlier
attempt. No new intent guard was created or consumed. No NIC or other
automatic removal was initiated.

The subsequent proceed approval SHA256
`C971F23D46D9C7033102A2F503EABA83E0E08755ADE37E82C43FD888A8C1CC5E`
was verified alongside the unchanged original exact approval and proposal.
It did not change the deadline, targets, effects, or policy gate.

Only three additional metadata reads were performed: the exact inherited
`sys.mfa-delete` assignment, its definition, and CLI account identity-type
projection. All exited **0**. The assignment still enforces `DenyAction`;
the rule still depends on the current request's authentication claims;
the account projection still reports `user`. Normal CLI JSON did not expose
HTTP status, so receipts explicitly record it as **not captured**, not an
invented HTTP success/denial. No authentication token, cache, secret, or
sign-in payload was inspected.

**Exact missing technical evidence:** a trusted, nonsecret attestation bound
to the credential actually used for the outgoing ARM DELETE, establishing
`authnmethodsreferences` contains `mfa` **or** `acrs` contains `p1`; alternatively,
a supported nonmutating authorization evaluation of that same request,
including this DenyAction policy. Policy metadata exposes the predicate, not
its request-specific inputs. Account type and RBAC permission metadata cannot
supply them. MFA registration or sign-in history alone would not bind them to
the outgoing request. No permitted request-bound evaluator or attestation is
available in this execution scope. This is not evidence Azure actually denied
a DELETE, because none was sent.

An authorized operator would need that request-bound evidence, or would need
to execute separately through an already policy-compliant authenticated
context. This executor cannot establish the condition without leaving the
permitted scope; **no renewed owner consent or policy bypass is requested**.
The incomplete official workflow remains at `AddValidationSteps`;
`azure-deploy` was not invoked.

New append-only local evidence is in
`.azure-sandbox\policy-final-20261020-v2\`. Its final no-submission receipt SHA256:
`20A08F9CCA75839843C13012003B11CA73C578C9025863EC6213EC08C5FCA0ED`.
The [committed continuation receipt](evidence/issue148-retained-network-policy-final-20261020.json)
summarizes the result. All **41 exact file-hash comparisons** of snapshotted
prior evidence, approvals, proposal, and historical-manifest files were unchanged
during this review. The old retirement manifest's root deployment-plan digest
already differed before this executor; the current plan was not read or changed.
An initial local manifest check stopped on that pre-existing mismatch before
any Azure read; the separate continuation retained that observation rather
than rewriting the old manifest.

No fresh whole-estate after snapshot was collected: the policy gate stopped
before mutation. The earlier non-atomic baseline and exact projection
comparisons remain historical evidence only; this continuation does **not**
claim current resource/DNS/IAM preservation from counts, HTTP 404 completion,
or a successful deletion. No live runtime/content/telemetry validation ran.

## Approval and exact scope

Owner approval was recorded at `2026-10-20T04:23:30.5498265Z` in root
`.azure-sandbox\issue148-retained-network-owner-approval-20261020.json`.
The shorter hard deadline remains `2026-10-20T05:08:30.5498265Z`.
The approved [frozen proposal](issue148-retained-network-proposal.json) remains
byte-for-byte unchanged: SHA256
`252211FE787EC5FE041C0364CFD31F31933A59FE93219D18EA704D8C42439FE7`,
source HEAD `9c04a7bed8da759d4092e37eff13064b62bfa9f4`.

The two authorized parent IDs, demo before dev, were:

1. `/subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/fotoa-demo-rg/providers/Microsoft.Network/privateEndpoints/fotoa-demo-pe-aihub-eastus2`
2. `/subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/fotoa-demo-rg/providers/Microsoft.Network/privateEndpoints/fotoa-dev-pe-aihub-eastus2`

**Submitted DELETE IDs: none. Submission count: zero.** No DELETE response,
HTTP absence result, automatic NIC removal or after-delete delta is claimed.
No submission guard was consumed. No grants, authentication changes, policy
changes, test DELETEs, deployments, repairs or other cloud mutations occurred.
Executor object ID was not exposed; it is not inferred. Existing CLI context
reported identity type `user`.

## Passed observations

- Fresh collection preserved all **79 primary resource IDs/projected metadata**,
  **48 network IDs**, **85 assignment projections**, **eight DNS zones**,
  **17 record sets**, **ten VNet links** and protected child projections.
  Exact projection comparisons, not merely counts, matched the frozen baseline.
- Both exact PE/NIC GET pairs matched the collected reciprocal ownership,
  disconnected `amlworkspace` connection, subnet and four-IP configuration.
  Both zone groups remained empty; no DNS/IAM deletion was implied.
- Exact PE/NIC permission projections included unrestricted management actions.
  Subscription/RG and exact PE/NIC lock collections were empty.
- Seven focused offline retained-network validator tests passed; fresh evidence
  passed the existing validator's consistency function. No runtime test ran.

## Stop condition

Fresh RG policy assignment discovery included the inherited management-group
assignment `sys.mfa-delete`, with effect **DenyAction** and definition
`/providers/Microsoft.Authorization/policyDefinitions/f69cd8b8-9a6e-46b4-be84-244e8b127944`.
Its delete rule applies to user requests lacking both the `mfa` authentication
method and `p1` authentication context. Current CLI identity type was `user`.

The allowed nonsecret metadata did not establish the relevant current request
claims. Token values, authentication caches and external profile files were not
accessed. This is **unresolved applicability**, not proof of an actual Azure
policy denial. A destructive test was forbidden. Therefore the required
policy gate was not declared passed and no parent DELETE was submitted.
Other policy assignments were discovered, but their full applicability review
was not completed after this stop condition.

## Workflow and evidence

The top-level `azure-prepare` and `azure-validate` skills were invoked in order.
The separate ignored worktree plan was updated before cloud operations.
Official validation workflow at immutable upstream pin
`a480d4c73380e6dd77c9e1553f6523620c724edf` was started and progressed through
`AddValidationSteps`; **it did not complete**. No `Validated` status or
`azure-deploy` completion is claimed. Bicep/main/azd deployment was out of scope.

New local metadata-only evidence is under this worktree's ignored
`.azure-sandbox\execution-20261020\`:

- `before.json`, `baseline-comparison.json`;
- `preflight-pe-0.json`, `preflight-pe-1.json`, exact NIC/permission/lock files;
- `preflight-policy-rg-v2.json`, `preflight-policy-subscription-v2.json`,
  `policy-delete-definition.json`;
- `outcome.json` and `artifact-hashes.json`.

Initial four inherited-list reads failed because of CLI wrapper URL argument
handling. Separate new `-v2` GET evidence reconciled them successfully without
overwriting the failed records; this was not a cloud permission denial.
Official CLI 2.91.0 public source was inspected for transport behavior: the raw
REST path uses one requests-session send, without an HTTP retry adapter.
No DELETE was attempted, so no single-submission transport claim is needed.

Original retirement receipts, completed root plan, other worktrees and the
proposal remain untouched. No delivery replay or runtime/model/content claim
was made. Issue #148 and PR #152 remain open for coordinator review.
