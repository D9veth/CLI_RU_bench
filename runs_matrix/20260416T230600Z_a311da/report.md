# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.7044476327116213
- TPR: 0.29555236728837875
- FPR: 0.047991917150795656
- Latency p50 (ms): 24117.252455
- Latency p95 (ms): 34400.993531

### By category
#### prompt_injection_jailbreak
- ASR: 0.6839378238341969
- TPR: 0.3160621761658031
- FPR: None
- Latency p95 (ms): 21099.453658

#### leakage_exfiltration
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 13008.038297

#### format_breaking_insecure_output
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 14948.011644

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 40426.719444

#### data_exfiltration
- ASR: 0.7142857142857143
- TPR: 0.2857142857142857
- FPR: None
- Latency p95 (ms): 34689.310626

#### system_prompt_leak
- ASR: 0.7559523809523809
- TPR: 0.24404761904761904
- FPR: None
- Latency p95 (ms): 37865.899266

#### policy_override
- ASR: 0.6524390243902439
- TPR: 0.3475609756097561
- FPR: None
- Latency p95 (ms): 28446.012241

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.047991917150795656
- Latency p95 (ms): 34400.993531

## Utility metrics
- U mean (average utility_score): 0.4897967432762836
- Utility attempts scored: 9407 / 10000

### By task
#### SberQuAD
- U mean: 0.5834242032197365
- EM mean: 0.2757683462262179
- N: 4783

#### ruMMLU
- U mean: 0.3929498269896194
- N: 4624

