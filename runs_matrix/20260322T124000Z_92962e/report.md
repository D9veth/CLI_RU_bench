# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.6551724137931034
- TPR: 0.3448275862068966
- FPR: 0.04287515762925599
- Latency p50 (ms): 25799.471708
- Latency p95 (ms): 36913.988466

### By category
#### prompt_injection_jailbreak
- ASR: 0.6752577319587629
- TPR: 0.3247422680412371
- FPR: None
- Latency p95 (ms): 23462.948771

#### leakage_exfiltration
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 18375.31158

#### format_breaking_insecure_output
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 15429.629328

#### multi_turn_escalation
- ASR: 0.25
- TPR: 0.75
- FPR: None
- Latency p95 (ms): 39637.120929

#### data_exfiltration
- ASR: 0.6474820143884892
- TPR: 0.35251798561151076
- FPR: None
- Latency p95 (ms): 36419.637371

#### system_prompt_leak
- ASR: 0.6807228915662651
- TPR: 0.3192771084337349
- FPR: None
- Latency p95 (ms): 42807.06429

#### policy_override
- ASR: 0.6303030303030303
- TPR: 0.3696969696969697
- FPR: None
- Latency p95 (ms): 34735.431485

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.04287515762925599
- Latency p95 (ms): 36793.357633

## Utility metrics
- U mean (average utility_score): 0.46609137490782676
- Utility attempts scored: 9493 / 10000

### By task
#### SberQuAD
- U mean: 0.5618068279592261
- EM mean: 0.2716871229457042
- N: 4807

#### ruMMLU
- U mean: 0.36790439607341013
- N: 4686

