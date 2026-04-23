# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.4763271162123386
- TPR: 0.5236728837876614
- FPR: 0.07665064507968632
- Latency p50 (ms): 23309.848681
- Latency p95 (ms): 33285.573714

### By category
#### prompt_injection_jailbreak
- ASR: 0.5412371134020618
- TPR: 0.4587628865979381
- FPR: None
- Latency p95 (ms): 21556.539151

#### leakage_exfiltration
- ASR: 0.5625
- TPR: 0.4375
- FPR: None
- Latency p95 (ms): 15254.656458

#### format_breaking_insecure_output
- ASR: 0.5454545454545454
- TPR: 0.45454545454545453
- FPR: None
- Latency p95 (ms): 14717.898114

#### multi_turn_escalation
- ASR: 0.25
- TPR: 0.75
- FPR: None
- Latency p95 (ms): 38534.335981

#### data_exfiltration
- ASR: 0.45
- TPR: 0.55
- FPR: None
- Latency p95 (ms): 34951.294306

#### system_prompt_leak
- ASR: 0.47904191616766467
- TPR: 0.5209580838323353
- FPR: None
- Latency p95 (ms): 37892.14982

#### policy_override
- ASR: 0.4121212121212121
- TPR: 0.5878787878787879
- FPR: None
- Latency p95 (ms): 29433.475609

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.07665064507968632
- Latency p95 (ms): 33192.32667

## Utility metrics
- U mean (average utility_score): 0.3373816693636562
- Utility attempts scored: 9146 / 10000

### By task
#### SberQuAD
- U mean: 0.4167073823405154
- EM mean: 0.17997465145754118
- N: 4734

#### ruMMLU
- U mean: 0.25226654578422486
- N: 4412

