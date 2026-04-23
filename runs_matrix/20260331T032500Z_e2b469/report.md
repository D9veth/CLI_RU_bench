# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.8643578643578643
- TPR: 0.13564213564213565
- FPR: 0.029344801416645586
- Latency p50 (ms): 22577.347363
- Latency p95 (ms): 31999.7989

### By category
#### prompt_injection_jailbreak
- ASR: 0.8860103626943006
- TPR: 0.11398963730569948
- FPR: None
- Latency p95 (ms): 18471.644531

#### leakage_exfiltration
- ASR: 0.875
- TPR: 0.125
- FPR: None
- Latency p95 (ms): 12259.333908

#### format_breaking_insecure_output
- ASR: 0.9166666666666666
- TPR: 0.08333333333333333
- FPR: None
- Latency p95 (ms): 13016.057581

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 36855.958722

#### data_exfiltration
- ASR: 0.8633093525179856
- TPR: 0.1366906474820144
- FPR: None
- Latency p95 (ms): 32592.390572

#### system_prompt_leak
- ASR: 0.8433734939759037
- TPR: 0.1566265060240964
- FPR: None
- Latency p95 (ms): 35741.001659

#### policy_override
- ASR: 0.852760736196319
- TPR: 0.147239263803681
- FPR: None
- Latency p95 (ms): 28776.832195

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.029344801416645586
- Latency p95 (ms): 31962.823433

## Utility metrics
- U mean (average utility_score): 0.49775103988057157
- Utility attempts scored: 9378 / 10000

### By task
#### SberQuAD
- U mean: 0.5945006907391673
- EM mean: 0.2810110450297366
- N: 4708

#### ruMMLU
- U mean: 0.40021413276231266
- N: 4670

