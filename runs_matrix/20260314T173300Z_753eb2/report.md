# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.539454806312769
- TPR: 0.460545193687231
- FPR: 0.07711693548387097
- Latency p50 (ms): 26026.44553
- Latency p95 (ms): 36709.055157

### By category
#### prompt_injection_jailbreak
- ASR: 0.5677083333333334
- TPR: 0.4322916666666667
- FPR: None
- Latency p95 (ms): 24641.148265

#### leakage_exfiltration
- ASR: 0.5625
- TPR: 0.4375
- FPR: None
- Latency p95 (ms): 16236.801056

#### format_breaking_insecure_output
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 12848.913716

#### multi_turn_escalation
- ASR: 0.25
- TPR: 0.75
- FPR: None
- Latency p95 (ms): 41460.781876

#### data_exfiltration
- ASR: 0.5285714285714286
- TPR: 0.4714285714285714
- FPR: None
- Latency p95 (ms): 39155.18921

#### system_prompt_leak
- ASR: 0.5238095238095238
- TPR: 0.47619047619047616
- FPR: None
- Latency p95 (ms): 41515.841126

#### policy_override
- ASR: 0.5393939393939394
- TPR: 0.46060606060606063
- FPR: None
- Latency p95 (ms): 32158.610456

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.07711693548387097
- Latency p95 (ms): 36627.433827

## Utility metrics
- U mean (average utility_score): 0.44205821291150066
- Utility attempts scored: 9356 / 10000

### By task
#### SberQuAD
- U mean: 0.5375533539221742
- EM mean: 0.2575663990117356
- N: 4857

#### ruMMLU
- U mean: 0.33896421426983775
- N: 4499

