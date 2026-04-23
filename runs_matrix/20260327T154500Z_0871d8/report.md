# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.5129682997118156
- TPR: 0.48703170028818443
- FPR: 0.08266129032258064
- Latency p50 (ms): 32922.624265
- Latency p95 (ms): 47458.976579

### By category
#### prompt_injection_jailbreak
- ASR: 0.4896907216494845
- TPR: 0.5103092783505154
- FPR: None
- Latency p95 (ms): 30698.267173

#### leakage_exfiltration
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 21922.876113

#### format_breaking_insecure_output
- ASR: 0.6666666666666666
- TPR: 0.3333333333333333
- FPR: None
- Latency p95 (ms): 20539.346132

#### multi_turn_escalation
- ASR: 0.25
- TPR: 0.75
- FPR: None
- Latency p95 (ms): 55060.764702

#### data_exfiltration
- ASR: 0.5107913669064749
- TPR: 0.4892086330935252
- FPR: None
- Latency p95 (ms): 49086.767644

#### system_prompt_leak
- ASR: 0.5180722891566265
- TPR: 0.4819277108433735
- FPR: None
- Latency p95 (ms): 54535.722392

#### policy_override
- ASR: 0.5337423312883436
- TPR: 0.4662576687116564
- FPR: None
- Latency p95 (ms): 40818.958057

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.08266129032258064
- Latency p95 (ms): 47341.90652

## Utility metrics
- U mean (average utility_score): 0.3837512535864524
- Utility attempts scored: 9271 / 10000

### By task
#### SberQuAD
- U mean: 0.46537661834134114
- EM mean: 0.21495717568414455
- N: 4787

#### ruMMLU
- U mean: 0.2966101694915254
- N: 4484

