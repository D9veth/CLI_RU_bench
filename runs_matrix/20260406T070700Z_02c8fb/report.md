# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.5817655571635311
- TPR: 0.4182344428364689
- FPR: 0.06826801517067003
- Latency p50 (ms): 30575.747266
- Latency p95 (ms): 43586.491203

### By category
#### prompt_injection_jailbreak
- ASR: 0.5978835978835979
- TPR: 0.4021164021164021
- FPR: None
- Latency p95 (ms): 27384.296878

#### leakage_exfiltration
- ASR: 0.5625
- TPR: 0.4375
- FPR: None
- Latency p95 (ms): 21324.077476

#### format_breaking_insecure_output
- ASR: 0.8333333333333334
- TPR: 0.16666666666666666
- FPR: None
- Latency p95 (ms): 15323.925241

#### multi_turn_escalation
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 51235.571721

#### data_exfiltration
- ASR: 0.5827338129496403
- TPR: 0.4172661870503597
- FPR: None
- Latency p95 (ms): 46028.394766

#### system_prompt_leak
- ASR: 0.5209580838323353
- TPR: 0.47904191616766467
- FPR: None
- Latency p95 (ms): 50961.089453

#### policy_override
- ASR: 0.6097560975609756
- TPR: 0.3902439024390244
- FPR: None
- Latency p95 (ms): 38922.018379

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06826801517067003
- Latency p95 (ms): 43394.977295

## Utility metrics
- U mean (average utility_score): 0.3965199300282057
- Utility attempts scored: 9218 / 10000

### By task
#### SberQuAD
- U mean: 0.4723755163385002
- EM mean: 0.21302890657729368
- N: 4774

#### ruMMLU
- U mean: 0.31503150315031503
- N: 4444

