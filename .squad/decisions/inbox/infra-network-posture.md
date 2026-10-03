# Decision: Network posture for Milestone 1 infrastructure (issue #21)

**Author:** Infra (Infrastructure/DevOps Engineer)
**Date:** 2026-10-02
**Related:** issue #21, PR (branch `squad/21-network-requirements`), `infra/modules/networking.bicep`, `infra/README.md` ("Network posture")

## Decision

The default/baseline network posture for all Milestone 1 infrastructure
(`infra/main.bicep` with default parameters) is **public network access,
secured by Azure AD/RBAC authentication and managed identity** - no VNet,
no private endpoints, no private DNS zones. This is the posture every other
Infra PR in this milestone (#15 Foundry project, #16 App Insights/Log
Analytics, #18 Key Vault) assumes and was built against.

An **optional, parameterized private-endpoint upgrade path** was added in
`infra/modules/networking.bicep` and wired into `main.bicep` behind a single
boolean parameter, `enablePrivateEndpoints` (default `false`). When set to
`true`, it additionally provisions private endpoints for the Key Vault
(`groupId: vault`) and the Foundry project (`groupId: amlworkspace`), either
into a small scratch VNet/subnet created by the module or into an existing
subnet supplied via `networkExistingSubnetResourceId`.

## Rationale

This repo is a sales-engineering/demo pipeline using **synthetic data only**
(see `/.github/copilot-instructions.md` section 1). Requiring network
isolation (VNet, private DNS, VPN/ExpressRoute/bastion connectivity) to spin
up a demo adds setup friction with no corresponding security benefit when
no real customer data is involved, and every resource already enforces
Azure AD/RBAC auth regardless of network reachability - "public" here means
"reachable", not "unauthenticated."

Network isolation becomes a legitimate requirement once a prospect wants a
real POC/pilot using their own data. The optional module exists for exactly
that scenario, without forcing every demo deployer to pay the setup cost.

## Coordination notes for other squad members

- **Lead / Agent (Prompt Agent, downstream code):** no change to any
  resource name, endpoint shape, or output contract from #15/#16/#18 - the
  private-endpoint variant does not rename or restructure the Foundry
  project, Key Vault, or App Insights resources. It only adds network
  reachability restrictions when explicitly enabled. Downstream code
  should keep using the same `foundryProjectEndpoint` /
  `keyVaultName` outputs either way; if `enablePrivateEndpoints: true` is
  used in a given environment, whoever runs that deployment must also run
  from inside (or peered with) the target VNet/subnet, or resolution of
  those endpoints will fail from outside the network perimeter.
- **Reviewers:** the private-endpoint variant (`main.parameters.private-endpoint.json`)
  was reviewed for Bicep syntax correctness only. It was **not**
  deployed/torn down against a live Azure subscription from the automated
  environment that authored it (no `az` CLI/subscription access available
  there - see PR "Current Limitations"). Please validate deploy + teardown
  of that variant against a scratch resource group before treating it as
  demo-ready, and record the result as a follow-up note here or in
  `.squad/decisions.md`.
- **Scribe:** please merge this into the shared decisions file alongside
  the Milestone 1 completion decision (`infra-milestone1-complete.md`).

## Status

Implemented and documented in PR for issue #21 (branch
`squad/21-network-requirements`). Default posture unchanged for all
existing/default deployments; opt-in only.
