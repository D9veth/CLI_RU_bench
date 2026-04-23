# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.7064748201438849
- TPR: 0.2935251798561151
- FPR: 0.043205224817884955
- Latency p50 (ms): 23256.342781
- Latency p95 (ms): 33442.882102

### By category
#### prompt_injection_jailbreak
- ASR: 0.7564766839378239
- TPR: 0.24352331606217617
- FPR: None
- Latency p95 (ms): 21429.823939

#### leakage_exfiltration
- ASR: 0.6875
- TPR: 0.3125
- FPR: None
- Latency p95 (ms): 14498.299533

#### format_breaking_insecure_output
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 10511.354802

#### multi_turn_escalation
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 39096.900744

#### data_exfiltration
- ASR: 0.6906474820143885
- TPR: 0.30935251798561153
- FPR: None
- Latency p95 (ms): 32729.027747

#### system_prompt_leak
- ASR: 0.7108433734939759
- TPR: 0.2891566265060241
- FPR: None
- Latency p95 (ms): 37255.014867

#### policy_override
- ASR: 0.6606060606060606
- TPR: 0.3393939393939394
- FPR: None
- Latency p95 (ms): 27546.23487

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.043205224817884955
- Latency p95 (ms): 33414.888493

## Utility metrics
- U mean (average utility_score): 0.4742697363854918
- Utility attempts scored: 9567 / 10000

### By task
#### SberQuAD
- U mean: 0.571027511431514
- EM mean: 0.2659114315139032
- N: 4855

#### ruMMLU
- U mean: 0.37457555178268254
- N: 4712

