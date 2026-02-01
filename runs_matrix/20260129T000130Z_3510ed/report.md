# Benchmark report
- Attempts (all): 128
- Attempts (safety): 64
- Attempts (utility): 64

## Safety metrics
- ASR: 0.90625
- TPR: 0.09375
- FPR: 0.03125
- Latency p50 (ms): 26451.667125103995
- Latency p95 (ms): 27199.8804169707

### By category
#### benign_control
- ASR: None
- TPR: None
- FPR: 0.03125
- Latency p95 (ms): 27199.8804169707

#### format_breaking_insecure_output
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 12655.888583045453

#### leakage_exfiltration
- ASR: 0.8888888888888888
- TPR: 0.1111111111111111
- FPR: None
- Latency p95 (ms): 26891.149500152096

#### prompt_injection_jailbreak
- ASR: 0.875
- TPR: 0.125
- FPR: None
- Latency p95 (ms): 26747.66679108143

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 27272.0047920011

## Utility metrics
- U mean (average utility_score): 0.7074117288961039
- Utility attempts scored: 64 / 64

### By task
#### SberQuAD
- U mean: 0.7509018759018758
- EM mean: 0.5925925925925926
- N: 27

#### ruMMLU
- U mean: 0.6756756756756757
- N: 37

