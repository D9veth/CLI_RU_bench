# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.7381294964028777
- TPR: 0.26187050359712233
- FPR: 0.03786922494319616
- Latency p50 (ms): 25228.887268
- Latency p95 (ms): 36586.876429

### By category
#### prompt_injection_jailbreak
- ASR: 0.7422680412371134
- TPR: 0.25773195876288657
- FPR: None
- Latency p95 (ms): 23480.988451

#### leakage_exfiltration
- ASR: 0.8
- TPR: 0.2
- FPR: None
- Latency p95 (ms): 17905.76916

#### format_breaking_insecure_output
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 13637.721434

#### multi_turn_escalation
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 43292.821082

#### data_exfiltration
- ASR: 0.7642857142857142
- TPR: 0.2357142857142857
- FPR: None
- Latency p95 (ms): 39202.31155

#### system_prompt_leak
- ASR: 0.7485029940119761
- TPR: 0.25149700598802394
- FPR: None
- Latency p95 (ms): 42308.438939

#### policy_override
- ASR: 0.6932515337423313
- TPR: 0.3067484662576687
- FPR: None
- Latency p95 (ms): 30522.391344

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.03786922494319616
- Latency p95 (ms): 36454.222849

## Utility metrics
- U mean (average utility_score): 0.44607774774104386
- Utility attempts scored: 9407 / 10000

### By task
#### SberQuAD
- U mean: 0.5373666960269077
- EM mean: 0.26235022072734915
- N: 4757

#### ruMMLU
- U mean: 0.35268817204301073
- N: 4650

