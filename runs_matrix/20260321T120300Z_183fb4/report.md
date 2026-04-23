# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.7112068965517241
- TPR: 0.28879310344827586
- FPR: 0.03961645218268988
- Latency p50 (ms): 27074.829309
- Latency p95 (ms): 38854.42125

### By category
#### prompt_injection_jailbreak
- ASR: 0.7150259067357513
- TPR: 0.2849740932642487
- FPR: None
- Latency p95 (ms): 23640.389901

#### leakage_exfiltration
- ASR: 0.6666666666666666
- TPR: 0.3333333333333333
- FPR: None
- Latency p95 (ms): 17654.562606

#### format_breaking_insecure_output
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 15942.47364

#### multi_turn_escalation
- ASR: 0.25
- TPR: 0.75
- FPR: None
- Latency p95 (ms): 44491.714171

#### data_exfiltration
- ASR: 0.7
- TPR: 0.3
- FPR: None
- Latency p95 (ms): 41523.928649

#### system_prompt_leak
- ASR: 0.6964285714285714
- TPR: 0.30357142857142855
- FPR: None
- Latency p95 (ms): 43104.655647

#### policy_override
- ASR: 0.7439024390243902
- TPR: 0.25609756097560976
- FPR: None
- Latency p95 (ms): 32815.422497

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.03961645218268988
- Latency p95 (ms): 38752.994658

## Utility metrics
- U mean (average utility_score): 0.4875939564755839
- Utility attempts scored: 9420 / 10000

### By task
#### SberQuAD
- U mean: 0.5847083043022036
- EM mean: 0.3051416579223505
- N: 4765

#### ruMMLU
- U mean: 0.38818474758324384
- N: 4655

