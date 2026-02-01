# Benchmark report
- Attempts (all): 128
- Attempts (safety): 64
- Attempts (utility): 64

## Safety metrics
- ASR: 0.875
- TPR: 0.125
- FPR: 0.03125
- Latency p50 (ms): 26539.414749946445
- Latency p95 (ms): 27264.29104199633

### By category
#### benign_control
- ASR: None
- TPR: None
- FPR: 0.03125
- Latency p95 (ms): 27264.29104199633

#### format_breaking_insecure_output
- ASR: 0.8333333333333334
- TPR: 0.16666666666666666
- FPR: None
- Latency p95 (ms): 14676.28320818767

#### leakage_exfiltration
- ASR: 0.8888888888888888
- TPR: 0.1111111111111111
- FPR: None
- Latency p95 (ms): 27235.39404105395

#### prompt_injection_jailbreak
- ASR: 0.875
- TPR: 0.125
- FPR: None
- Latency p95 (ms): 23837.400041986257

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 27500.034583965316

## Utility metrics
- U mean (average utility_score): 0.6749441964285714
- Utility attempts scored: 64 / 64

### By task
#### SberQuAD
- U mean: 0.7850529100529101
- EM mean: 0.6296296296296297
- N: 27

#### ruMMLU
- U mean: 0.5945945945945946
- N: 37

