# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.5774240231548481
- TPR: 0.42257597684515197
- FPR: 0.06559031281533804
- Latency p50 (ms): 30378.019239
- Latency p95 (ms): 43364.042464

### By category
#### prompt_injection_jailbreak
- ASR: 0.5625
- TPR: 0.4375
- FPR: None
- Latency p95 (ms): 27440.57257

#### leakage_exfiltration
- ASR: 0.4375
- TPR: 0.5625
- FPR: None
- Latency p95 (ms): 22284.268796

#### format_breaking_insecure_output
- ASR: 0.7272727272727273
- TPR: 0.2727272727272727
- FPR: None
- Latency p95 (ms): 18432.557806

#### multi_turn_escalation
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 48499.919531

#### data_exfiltration
- ASR: 0.6258992805755396
- TPR: 0.37410071942446044
- FPR: None
- Latency p95 (ms): 44964.025832

#### system_prompt_leak
- ASR: 0.5481927710843374
- TPR: 0.45180722891566266
- FPR: None
- Latency p95 (ms): 50213.204808

#### policy_override
- ASR: 0.588957055214724
- TPR: 0.4110429447852761
- FPR: None
- Latency p95 (ms): 36932.487018

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06559031281533804
- Latency p95 (ms): 43140.880083

## Utility metrics
- U mean (average utility_score): 0.38897291912958754
- Utility attempts scored: 9237 / 10000

### By task
#### SberQuAD
- U mean: 0.47203506809583856
- EM mean: 0.1971416561580496
- N: 4758

#### ruMMLU
- U mean: 0.30073677160080375
- N: 4479

