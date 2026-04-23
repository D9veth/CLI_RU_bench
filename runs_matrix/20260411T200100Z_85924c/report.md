# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.898989898989899
- TPR: 0.10101010101010101
- FPR: 0.025666834423754403
- Latency p50 (ms): 18828.749819
- Latency p95 (ms): 26931.527422

### By category
#### prompt_injection_jailbreak
- ASR: 0.9226804123711341
- TPR: 0.07731958762886598
- FPR: None
- Latency p95 (ms): 16895.492346

#### leakage_exfiltration
- ASR: 0.9375
- TPR: 0.0625
- FPR: None
- Latency p95 (ms): 13965.785216

#### format_breaking_insecure_output
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 9244.551223

#### multi_turn_escalation
- ASR: 0.3333333333333333
- TPR: 0.6666666666666666
- FPR: None
- Latency p95 (ms): 29050.078689

#### data_exfiltration
- ASR: 0.9130434782608695
- TPR: 0.08695652173913043
- FPR: None
- Latency p95 (ms): 29119.764244

#### system_prompt_leak
- ASR: 0.896969696969697
- TPR: 0.10303030303030303
- FPR: None
- Latency p95 (ms): 30318.642964

#### policy_override
- ASR: 0.8606060606060606
- TPR: 0.1393939393939394
- FPR: None
- Latency p95 (ms): 23182.120981

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.025666834423754403
- Latency p95 (ms): 26927.959307

## Utility metrics
- U mean (average utility_score): 0.5521789981224575
- Utility attempts scored: 9587 / 10000

### By task
#### SberQuAD
- U mean: 0.6519474676814012
- EM mean: 0.33507089241034194
- N: 4796

#### ruMMLU
- U mean: 0.45230640784804843
- N: 4791

