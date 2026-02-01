# Benchmark report
- Attempts (all): 128
- Attempts (safety): 64
- Attempts (utility): 64

## Safety metrics
- ASR: 0.84375
- TPR: 0.15625
- FPR: 0.0
- Latency p50 (ms): 26766.11370802857
- Latency p95 (ms): 28565.00104116276

### By category
#### benign_control
- ASR: None
- TPR: None
- FPR: 0.0
- Latency p95 (ms): 28709.488708060235

#### format_breaking_insecure_output
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 11805.745207937434

#### leakage_exfiltration
- ASR: 0.8888888888888888
- TPR: 0.1111111111111111
- FPR: None
- Latency p95 (ms): 28508.6216670461

#### prompt_injection_jailbreak
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 27246.876707999036

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 27553.384291008115

## Utility metrics
- U mean (average utility_score): 0.705078125
- Utility attempts scored: 64 / 64

### By task
#### SberQuAD
- U mean: 0.8194444444444444
- EM mean: 0.6666666666666666
- N: 27

#### ruMMLU
- U mean: 0.6216216216216216
- N: 37

