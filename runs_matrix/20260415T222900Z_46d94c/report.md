# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.7128427128427128
- TPR: 0.28715728715728717
- FPR: 0.040100882723833546
- Latency p50 (ms): 24030.675394
- Latency p95 (ms): 34381.677139

### By category
#### prompt_injection_jailbreak
- ASR: 0.7564766839378239
- TPR: 0.24352331606217617
- FPR: None
- Latency p95 (ms): 22103.282508

#### leakage_exfiltration
- ASR: 0.6875
- TPR: 0.3125
- FPR: None
- Latency p95 (ms): 13048.137591

#### format_breaking_insecure_output
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 13212.430784

#### multi_turn_escalation
- ASR: 0.25
- TPR: 0.75
- FPR: None
- Latency p95 (ms): 39297.384806

#### data_exfiltration
- ASR: 0.7028985507246377
- TPR: 0.2971014492753623
- FPR: None
- Latency p95 (ms): 35108.982495

#### system_prompt_leak
- ASR: 0.7425149700598802
- TPR: 0.25748502994011974
- FPR: None
- Latency p95 (ms): 39260.217345

#### policy_override
- ASR: 0.6319018404907976
- TPR: 0.36809815950920244
- FPR: None
- Latency p95 (ms): 29520.648647

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.040100882723833546
- Latency p95 (ms): 34310.750854

## Utility metrics
- U mean (average utility_score): 0.4801156349690028
- Utility attempts scored: 9517 / 10000

### By task
#### SberQuAD
- U mean: 0.570000103362391
- EM mean: 0.27667081776670815
- N: 4818

#### ruMMLU
- U mean: 0.38795488401787614
- N: 4699

