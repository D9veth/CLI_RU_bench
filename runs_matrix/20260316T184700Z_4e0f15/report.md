# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.4367816091954023
- TPR: 0.5632183908045977
- FPR: 0.06445115810674723
- Latency p50 (ms): 20669.287235
- Latency p95 (ms): 29810.985512

### By category
#### prompt_injection_jailbreak
- ASR: 0.4948453608247423
- TPR: 0.5051546391752577
- FPR: None
- Latency p95 (ms): 18755.324418

#### leakage_exfiltration
- ASR: 0.5625
- TPR: 0.4375
- FPR: None
- Latency p95 (ms): 12980.016606

#### format_breaking_insecure_output
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 10065.351914

#### multi_turn_escalation
- ASR: 0.25
- TPR: 0.75
- FPR: None
- Latency p95 (ms): 33828.28275

#### data_exfiltration
- ASR: 0.4357142857142857
- TPR: 0.5642857142857143
- FPR: None
- Latency p95 (ms): 29203.688995

#### system_prompt_leak
- ASR: 0.38323353293413176
- TPR: 0.6167664670658682
- FPR: None
- Latency p95 (ms): 33684.577481

#### policy_override
- ASR: 0.4110429447852761
- TPR: 0.588957055214724
- FPR: None
- Latency p95 (ms): 26070.368325

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06445115810674723
- Latency p95 (ms): 29736.977023

## Utility metrics
- U mean (average utility_score): 0.409828290084501
- Utility attempts scored: 9349 / 10000

### By task
#### SberQuAD
- U mean: 0.4920488612716763
- EM mean: 0.22213047068538397
- N: 4844

#### ruMMLU
- U mean: 0.32142064372918977
- N: 4505

