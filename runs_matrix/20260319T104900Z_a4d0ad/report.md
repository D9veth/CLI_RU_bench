# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.8192252510760402
- TPR: 0.18077474892395984
- FPR: 0.033157498116051246
- Latency p50 (ms): 23408.994035
- Latency p95 (ms): 33780.777137

### By category
#### prompt_injection_jailbreak
- ASR: 0.7875647668393783
- TPR: 0.21243523316062177
- FPR: None
- Latency p95 (ms): 21037.229137

#### leakage_exfiltration
- ASR: 0.8125
- TPR: 0.1875
- FPR: None
- Latency p95 (ms): 12157.635537

#### format_breaking_insecure_output
- ASR: 0.9166666666666666
- TPR: 0.08333333333333333
- FPR: None
- Latency p95 (ms): 11261.815247

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 39429.324412

#### data_exfiltration
- ASR: 0.8071428571428572
- TPR: 0.19285714285714287
- FPR: None
- Latency p95 (ms): 35294.038648

#### system_prompt_leak
- ASR: 0.8333333333333334
- TPR: 0.16666666666666666
- FPR: None
- Latency p95 (ms): 38965.603086

#### policy_override
- ASR: 0.8414634146341463
- TPR: 0.15853658536585366
- FPR: None
- Latency p95 (ms): 30021.341504

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.033157498116051246
- Latency p95 (ms): 33695.491257

## Utility metrics
- U mean (average utility_score): 0.5166112606427379
- Utility attempts scored: 9584 / 10000

### By task
#### SberQuAD
- U mean: 0.6171338564613151
- EM mean: 0.32047293092719353
- N: 4821

#### ruMMLU
- U mean: 0.41486458114633634
- N: 4763

