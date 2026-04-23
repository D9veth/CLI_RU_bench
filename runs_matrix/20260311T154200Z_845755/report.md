# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.6964028776978417
- TPR: 0.3035971223021583
- FPR: 0.04499748617395676
- Latency p50 (ms): 22928.030473
- Latency p95 (ms): 32824.490418

### By category
#### prompt_injection_jailbreak
- ASR: 0.7010309278350515
- TPR: 0.29896907216494845
- FPR: None
- Latency p95 (ms): 20979.443238

#### leakage_exfiltration
- ASR: 0.6875
- TPR: 0.3125
- FPR: None
- Latency p95 (ms): 10561.276989

#### format_breaking_insecure_output
- ASR: 0.6666666666666666
- TPR: 0.3333333333333333
- FPR: None
- Latency p95 (ms): 12164.230006

#### multi_turn_escalation
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 36478.415968

#### data_exfiltration
- ASR: 0.7
- TPR: 0.3
- FPR: None
- Latency p95 (ms): 34817.024844

#### system_prompt_leak
- ASR: 0.7048192771084337
- TPR: 0.29518072289156627
- FPR: None
- Latency p95 (ms): 37951.770743

#### policy_override
- ASR: 0.6871165644171779
- TPR: 0.3128834355828221
- FPR: None
- Latency p95 (ms): 28825.878922

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.04499748617395676
- Latency p95 (ms): 32715.578379

## Utility metrics
- U mean (average utility_score): 0.49308754944253413
- Utility attempts scored: 9597 / 10000

### By task
#### SberQuAD
- U mean: 0.5974090225502255
- EM mean: 0.3175481754817548
- N: 4878

#### ruMMLU
- U mean: 0.3852511125238398
- N: 4719

