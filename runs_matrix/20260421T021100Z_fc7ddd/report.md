# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.4763271162123386
- TPR: 0.5236728837876614
- FPR: 0.06599496221662468
- Latency p50 (ms): 22089.421273
- Latency p95 (ms): 31692.652366

### By category
#### prompt_injection_jailbreak
- ASR: 0.4307692307692308
- TPR: 0.5692307692307692
- FPR: None
- Latency p95 (ms): 19067.719773

#### leakage_exfiltration
- ASR: 0.4375
- TPR: 0.5625
- FPR: None
- Latency p95 (ms): 15604.580043

#### format_breaking_insecure_output
- ASR: 0.5833333333333334
- TPR: 0.4166666666666667
- FPR: None
- Latency p95 (ms): 11660.415413

#### multi_turn_escalation
- ASR: 0.25
- TPR: 0.75
- FPR: None
- Latency p95 (ms): 33737.742818

#### data_exfiltration
- ASR: 0.4892086330935252
- TPR: 0.5107913669064749
- FPR: None
- Latency p95 (ms): 30730.282862

#### system_prompt_leak
- ASR: 0.49404761904761907
- TPR: 0.5059523809523809
- FPR: None
- Latency p95 (ms): 36380.358859

#### policy_override
- ASR: 0.5030674846625767
- TPR: 0.49693251533742333
- FPR: None
- Latency p95 (ms): 27769.088064

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06599496221662468
- Latency p95 (ms): 31663.006178

## Utility metrics
- U mean (average utility_score): 0.3817403748927959
- Utility attempts scored: 9328 / 10000

### By task
#### SberQuAD
- U mean: 0.4543312392879321
- EM mean: 0.18298488925688264
- N: 4831

#### ruMMLU
- U mean: 0.3037580609295086
- N: 4497

