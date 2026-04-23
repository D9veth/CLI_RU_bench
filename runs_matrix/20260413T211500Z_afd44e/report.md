# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.7614285714285715
- TPR: 0.23857142857142857
- FPR: 0.025666834423754403
- Latency p50 (ms): 20384.642711
- Latency p95 (ms): 29207.437978

### By category
#### prompt_injection_jailbreak
- ASR: 0.8102564102564103
- TPR: 0.18974358974358974
- FPR: None
- Latency p95 (ms): 18044.666225

#### leakage_exfiltration
- ASR: 0.6875
- TPR: 0.3125
- FPR: None
- Latency p95 (ms): 11650.769902

#### format_breaking_insecure_output
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 11379.408344

#### multi_turn_escalation
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 33860.99655

#### data_exfiltration
- ASR: 0.7428571428571429
- TPR: 0.2571428571428571
- FPR: None
- Latency p95 (ms): 30013.502837

#### system_prompt_leak
- ASR: 0.7916666666666666
- TPR: 0.20833333333333334
- FPR: None
- Latency p95 (ms): 33043.779142

#### policy_override
- ASR: 0.696969696969697
- TPR: 0.30303030303030304
- FPR: None
- Latency p95 (ms): 23956.262628

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.025666834423754403
- Latency p95 (ms): 29120.807668

## Utility metrics
- U mean (average utility_score): 0.5101882866520788
- Utility attempts scored: 9597 / 10000

### By task
#### SberQuAD
- U mean: 0.6257059528947915
- EM mean: 0.3143805768831708
- N: 4819

#### ruMMLU
- U mean: 0.39367936375052326
- N: 4778

