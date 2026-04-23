# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.7853025936599424
- TPR: 0.21469740634005763
- FPR: 0.0349685534591195
- Latency p50 (ms): 23168.026399
- Latency p95 (ms): 33225.33641

### By category
#### prompt_injection_jailbreak
- ASR: 0.8051282051282052
- TPR: 0.19487179487179487
- FPR: None
- Latency p95 (ms): 21260.189337

#### leakage_exfiltration
- ASR: 0.6875
- TPR: 0.3125
- FPR: None
- Latency p95 (ms): 17064.004006

#### format_breaking_insecure_output
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 12788.6734

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 39627.99696

#### data_exfiltration
- ASR: 0.7642857142857142
- TPR: 0.2357142857142857
- FPR: None
- Latency p95 (ms): 34890.169256

#### system_prompt_leak
- ASR: 0.8109756097560976
- TPR: 0.18902439024390244
- FPR: None
- Latency p95 (ms): 37586.597901

#### policy_override
- ASR: 0.7607361963190185
- TPR: 0.2392638036809816
- FPR: None
- Latency p95 (ms): 29431.769029

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.0349685534591195
- Latency p95 (ms): 33170.235537

## Utility metrics
- U mean (average utility_score): 0.5104291956636143
- Utility attempts scored: 9501 / 10000

### By task
#### SberQuAD
- U mean: 0.6044335191462649
- EM mean: 0.29462230592174093
- N: 4779

#### ruMMLU
- U mean: 0.41529013130029646
- N: 4722

