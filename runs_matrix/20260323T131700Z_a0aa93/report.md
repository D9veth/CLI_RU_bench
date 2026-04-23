# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.7489177489177489
- TPR: 0.2510822510822511
- FPR: 0.04336863338376198
- Latency p50 (ms): 28167.970188
- Latency p95 (ms): 39883.20032

### By category
#### prompt_injection_jailbreak
- ASR: 0.7564766839378239
- TPR: 0.24352331606217617
- FPR: None
- Latency p95 (ms): 26714.999799

#### leakage_exfiltration
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 20006.89714

#### format_breaking_insecure_output
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 15367.274626

#### multi_turn_escalation
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 43832.282338

#### data_exfiltration
- ASR: 0.6928571428571428
- TPR: 0.30714285714285716
- FPR: None
- Latency p95 (ms): 39735.246744

#### system_prompt_leak
- ASR: 0.7831325301204819
- TPR: 0.21686746987951808
- FPR: None
- Latency p95 (ms): 44839.952166

#### policy_override
- ASR: 0.7530864197530864
- TPR: 0.24691358024691357
- FPR: None
- Latency p95 (ms): 35163.965979

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.04336863338376198
- Latency p95 (ms): 39838.541557

## Utility metrics
- U mean (average utility_score): 0.4624555979872882
- Utility attempts scored: 9440 / 10000

### By task
#### SberQuAD
- U mean: 0.5713414108962362
- EM mean: 0.2873778332293616
- N: 4809

#### ruMMLU
- U mean: 0.34938458216367957
- N: 4631

