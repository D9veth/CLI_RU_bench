# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.8653295128939829
- TPR: 0.1346704871060172
- FPR: 0.0198692152917505
- Latency p50 (ms): 18285.308153
- Latency p95 (ms): 26246.63129

### By category
#### prompt_injection_jailbreak
- ASR: 0.8814432989690721
- TPR: 0.11855670103092783
- FPR: None
- Latency p95 (ms): 16573.630967

#### leakage_exfiltration
- ASR: 0.875
- TPR: 0.125
- FPR: None
- Latency p95 (ms): 12236.070076

#### format_breaking_insecure_output
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 10365.283624

#### multi_turn_escalation
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 31097.871544

#### data_exfiltration
- ASR: 0.8785714285714286
- TPR: 0.12142857142857143
- FPR: None
- Latency p95 (ms): 26573.936199

#### system_prompt_leak
- ASR: 0.8802395209580839
- TPR: 0.11976047904191617
- FPR: None
- Latency p95 (ms): 29757.808369

#### policy_override
- ASR: 0.8303030303030303
- TPR: 0.1696969696969697
- FPR: None
- Latency p95 (ms): 23337.133509

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.0198692152917505
- Latency p95 (ms): 26172.431552

## Utility metrics
- U mean (average utility_score): 0.5619022150725832
- Utility attempts scored: 9713 / 10000

### By task
#### SberQuAD
- U mean: 0.6595593453237409
- EM mean: 0.35847893114080165
- N: 4865

#### ruMMLU
- U mean: 0.4639026402640264
- N: 4848

