# Synthetic Fixtures

**Policy: every file in this folder MUST contain only fabricated, synthetic data.**

- Never add real member IDs, patient data, real plan names, real addresses, or
  any content that resembles an actual healthcare payer's real customer data.
- Synthetic member IDs use the `SYN-` prefix (e.g. `SYN-00042`).
- Synthetic plan names are obviously fictional (e.g. "Acme Synthetic PPO").
- Every fixture is tagged `synthetic: true` in its metadata.

This policy is non-negotiable per `/.github/copilot-instructions.md` (§1, §19)
and applies to every example, test, and demo scenario in this repository.
