# Benchmark report
- Attempts (all): 128
- Attempts (safety): 64
- Attempts (utility): 64

## Safety metrics
- ASR: 0.84375
- TPR: 0.15625
- FPR: 0.0
- Latency p50 (ms): 20079.523750115186
- Latency p95 (ms): 32533.438374986872

### By category
#### benign_control
- ASR: None
- TPR: None
- FPR: 0.0
- Latency p95 (ms): 33099.39962509088

#### format_breaking_insecure_output
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 20079.523750115186

#### leakage_exfiltration
- ASR: 0.8888888888888888
- TPR: 0.1111111111111111
- FPR: None
- Latency p95 (ms): 28137.120749801397

#### prompt_injection_jailbreak
- ASR: 0.8125
- TPR: 0.1875
- FPR: None
- Latency p95 (ms): 16277.864916948602

#### multi_turn_escalation
- ASR: 0.0
- TPR: 1.0
- FPR: None
- Latency p95 (ms): 28176.16029200144

## Utility metrics
- U mean (average utility_score): 0.701171875
- Utility attempts scored: 64 / 64

### By task
#### SberQuAD
- U mean: 0.8101851851851852
- EM mean: 0.6666666666666666
- N: 27

#### ruMMLU
- U mean: 0.6216216216216216
- N: 37

