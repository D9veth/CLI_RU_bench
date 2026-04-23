# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.5014409221902018
- TPR: 0.49855907780979825
- FPR: 0.06636500754147813
- Latency p50 (ms): 25061.879511
- Latency p95 (ms): 36121.965102

### By category
#### prompt_injection_jailbreak
- ASR: 0.4587628865979381
- TPR: 0.5412371134020618
- FPR: None
- Latency p95 (ms): 22964.603575

#### leakage_exfiltration
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 14353.448936

#### format_breaking_insecure_output
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 14859.946322

#### multi_turn_escalation
- ASR: 0.3333333333333333
- TPR: 0.6666666666666666
- FPR: None
- Latency p95 (ms): 42399.114341

#### data_exfiltration
- ASR: 0.5285714285714286
- TPR: 0.4714285714285714
- FPR: None
- Latency p95 (ms): 37969.945532

#### system_prompt_leak
- ASR: 0.5121951219512195
- TPR: 0.4878048780487805
- FPR: None
- Latency p95 (ms): 40818.260578

#### policy_override
- ASR: 0.49696969696969695
- TPR: 0.503030303030303
- FPR: None
- Latency p95 (ms): 31880.312779

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06636500754147813
- Latency p95 (ms): 36055.882068

## Utility metrics
- U mean (average utility_score): 0.4267331688463583
- Utility attempts scored: 9405 / 10000

### By task
#### SberQuAD
- U mean: 0.5037089702048417
- EM mean: 0.22698117111524932
- N: 4833

#### ruMMLU
- U mean: 0.34536307961504814
- N: 4572

