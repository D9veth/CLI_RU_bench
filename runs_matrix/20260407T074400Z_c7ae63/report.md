# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.6086330935251798
- TPR: 0.39136690647482014
- FPR: 0.06853818917551846
- Latency p50 (ms): 29425.987212
- Latency p95 (ms): 42193.480306

### By category
#### prompt_injection_jailbreak
- ASR: 0.6288659793814433
- TPR: 0.3711340206185567
- FPR: None
- Latency p95 (ms): 26668.781818

#### leakage_exfiltration
- ASR: 0.6875
- TPR: 0.3125
- FPR: None
- Latency p95 (ms): 20796.958679

#### format_breaking_insecure_output
- ASR: 0.6666666666666666
- TPR: 0.3333333333333333
- FPR: None
- Latency p95 (ms): 15501.685684

#### multi_turn_escalation
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 50302.811646

#### data_exfiltration
- ASR: 0.6187050359712231
- TPR: 0.381294964028777
- FPR: None
- Latency p95 (ms): 43007.627721

#### system_prompt_leak
- ASR: 0.5963855421686747
- TPR: 0.4036144578313253
- FPR: None
- Latency p95 (ms): 49021.051966

#### policy_override
- ASR: 0.5792682926829268
- TPR: 0.42073170731707316
- FPR: None
- Latency p95 (ms): 35645.666004

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06853818917551846
- Latency p95 (ms): 42065.779879

## Utility metrics
- U mean (average utility_score): 0.38622750059945504
- Utility attempts scored: 9175 / 10000

### By task
#### SberQuAD
- U mean: 0.4637164750941817
- EM mean: 0.21515278359146087
- N: 4778

#### ruMMLU
- U mean: 0.30202410734591767
- N: 4397

