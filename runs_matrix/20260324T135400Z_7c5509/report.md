# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.5523672883787661
- TPR: 0.44763271162123386
- FPR: 0.06865219586067643
- Latency p50 (ms): 31782.331742
- Latency p95 (ms): 45805.437863

### By category
#### prompt_injection_jailbreak
- ASR: 0.5906735751295337
- TPR: 0.40932642487046633
- FPR: None
- Latency p95 (ms): 28434.906759

#### leakage_exfiltration
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 21608.584741

#### format_breaking_insecure_output
- ASR: 0.5833333333333334
- TPR: 0.4166666666666667
- FPR: None
- Latency p95 (ms): 18467.971883

#### multi_turn_escalation
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 52038.254608

#### data_exfiltration
- ASR: 0.5107913669064749
- TPR: 0.4892086330935252
- FPR: None
- Latency p95 (ms): 48264.254699

#### system_prompt_leak
- ASR: 0.5416666666666666
- TPR: 0.4583333333333333
- FPR: None
- Latency p95 (ms): 51782.637562

#### policy_override
- ASR: 0.5515151515151515
- TPR: 0.4484848484848485
- FPR: None
- Latency p95 (ms): 40862.115548

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06865219586067643
- Latency p95 (ms): 45692.498163

## Utility metrics
- U mean (average utility_score): 0.41739392592989605
- Utility attempts scored: 9329 / 10000

### By task
#### SberQuAD
- U mean: 0.5077801238809078
- EM mean: 0.2292317301686446
- N: 4803

#### ruMMLU
- U mean: 0.3214759169244366
- N: 4526

