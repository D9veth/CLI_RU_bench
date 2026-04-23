# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.5432276657060519
- TPR: 0.45677233429394815
- FPR: 0.06268882175226587
- Latency p50 (ms): 24912.232465
- Latency p95 (ms): 35561.874477

### By category
#### prompt_injection_jailbreak
- ASR: 0.5260416666666666
- TPR: 0.4739583333333333
- FPR: None
- Latency p95 (ms): 22850.442484

#### leakage_exfiltration
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 17040.653947

#### format_breaking_insecure_output
- ASR: 0.5833333333333334
- TPR: 0.4166666666666667
- FPR: None
- Latency p95 (ms): 11343.856602

#### multi_turn_escalation
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 38858.227588

#### data_exfiltration
- ASR: 0.5214285714285715
- TPR: 0.4785714285714286
- FPR: None
- Latency p95 (ms): 39019.970798

#### system_prompt_leak
- ASR: 0.5602409638554217
- TPR: 0.4397590361445783
- FPR: None
- Latency p95 (ms): 40076.815031

#### policy_override
- ASR: 0.5426829268292683
- TPR: 0.4573170731707317
- FPR: None
- Latency p95 (ms): 28423.400453

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06268882175226587
- Latency p95 (ms): 35397.780047

## Utility metrics
- U mean (average utility_score): 0.4464426824210526
- Utility attempts scored: 9500 / 10000

### By task
#### SberQuAD
- U mean: 0.527631893948718
- EM mean: 0.2541538461538462
- N: 4875

#### ruMMLU
- U mean: 0.36086486486486485
- N: 4625

