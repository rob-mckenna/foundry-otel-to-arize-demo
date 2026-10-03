# Sample Scenario Output (Synthetic)

Captured output from `python -m prompt_agent.main --scenarios`, run locally
against the stub model client (no live Foundry model call — see
`prompt_agent/model_client.py`'s `# STUB` comment). All data below is
synthetic demo content — no real member, plan, or claims data.

```
--- scenario: benefits-deductible-lookup (synthetic_member_id=SYN-00042) ---
prompt:    What is my synthetic deductible under Acme Synthetic PPO?
tool_out:  Acme Synthetic PPO — $500/$1,000 deductible, $25 PCP copay, in-network only after deductible.
response:  Your synthetic deductible under Acme Synthetic PPO is $500 individual / $1,000 family for this benefit year.
tokens:    prompt=26 completion=17 total=43

--- scenario: benefits-copay-lookup (synthetic_member_id=SYN-00077) ---
prompt:    What is my copay for a primary care visit on Acme Synthetic PPO?
tool_out:  Acme Synthetic PPO — $500/$1,000 deductible, $25 PCP copay, in-network only after deductible.
response:  Your synthetic primary care copay is $25 per visit under Acme Synthetic PPO.
tokens:    prompt=30 completion=13 total=43

--- scenario: member-id-confirmation (synthetic_member_id=SYN-00042) ---
prompt:    Can you confirm the member ID you have on file for me?
tool_out:  Acme Synthetic PPO — $500/$1,000 deductible, $25 PCP copay, in-network only after deductible.
response:  Your synthetic member ID on file is SYN-00042.
tokens:    prompt=29 completion=8 total=37

--- scenario: network-coverage-lookup (synthetic_member_id=SYN-00118) ---
prompt:    Is my primary care doctor in-network under Acme Synthetic HMO?
tool_out:  Acme Synthetic HMO — requires in-network PCP referral, $15 PCP copay, no out-of-network coverage.
response:  Acme Synthetic PPO covers in-network primary care visits at 100% after your deductible is met.
tokens:    prompt=28 completion=15 total=43

--- scenario: claim-status-lookup (synthetic_member_id=SYN-00077) ---
prompt:    What is the status of my most recent synthetic claim?
tool_out:  Acme Synthetic PPO — $500/$1,000 deductible, $25 PCP copay, in-network only after deductible.
response:  Your most recent synthetic claim (CLM-SYN-9001) was processed and paid in full.
tokens:    prompt=27 completion=12 total=39
```
