# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.9564586357039188
- TPR: 0.04354136429608128
- FPR: 0.02806573957016435
- Latency p50 (ms): 22236.144518
- Latency p95 (ms): 32037.660454

### By category
#### prompt_injection_jailbreak
- ASR: 0.9948186528497409
- TPR: 0.0051813471502590676
- FPR: None
- Latency p95 (ms): 19347.977903

#### leakage_exfiltration
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 13834.495036

#### format_breaking_insecure_output
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 11414.228457

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 36213.483481

#### data_exfiltration
- ASR: 0.9191176470588235
- TPR: 0.08088235294117647
- FPR: None
- Latency p95 (ms): 34892.518149

#### system_prompt_leak
- ASR: 0.963855421686747
- TPR: 0.03614457831325301
- FPR: None
- Latency p95 (ms): 36813.065028

#### policy_override
- ASR: 0.9506172839506173
- TPR: 0.04938271604938271
- FPR: None
- Latency p95 (ms): 27355.562421

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.02806573957016435
- Latency p95 (ms): 31898.901694

## Utility metrics
- U mean (average utility_score): 0.5107419825531915
- Utility attempts scored: 9400 / 10000

### By task
#### SberQuAD
- U mean: 0.5972758360237893
- EM mean: 0.2980033984706882
- N: 4708

#### ruMMLU
- U mean: 0.42391304347826086
- N: 4692

