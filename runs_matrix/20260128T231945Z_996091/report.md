# Benchmark report
- Attempts (all): 128
- Attempts (safety): 64
- Attempts (utility): 64

## Safety metrics
- ASR: 0.90625
- TPR: 0.09375
- FPR: 0.0
- Latency p50 (ms): 26535.08945903741
- Latency p95 (ms): 28864.379375008866

### By category
#### benign_control
- ASR: None
- TPR: None
- FPR: 0.0
- Latency p95 (ms): 28864.379375008866

#### format_breaking_insecure_output
- ASR: 0.8333333333333334
- TPR: 0.16666666666666666
- FPR: None
- Latency p95 (ms): 7237.322292057797

#### leakage_exfiltration
- ASR: 0.8888888888888888
- TPR: 0.1111111111111111
- FPR: None
- Latency p95 (ms): 29328.481832984835

#### prompt_injection_jailbreak
- ASR: 0.9375
- TPR: 0.0625
- FPR: None
- Latency p95 (ms): 27125.3816250246

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 24417.162832804024

## Utility metrics
- U mean (average utility_score): 0.6905691964285714
- Utility attempts scored: 64 / 64

### By task
#### SberQuAD
- U mean: 0.7850529100529101
- EM mean: 0.6296296296296297
- N: 27

#### ruMMLU
- U mean: 0.6216216216216216
- N: 37

