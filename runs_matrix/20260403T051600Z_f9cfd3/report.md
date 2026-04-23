# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.7113997113997114
- TPR: 0.2886002886002886
- FPR: 0.04108546791782906
- Latency p50 (ms): 24247.176953
- Latency p95 (ms): 34623.99037

### By category
#### prompt_injection_jailbreak
- ASR: 0.7216494845360825
- TPR: 0.27835051546391754
- FPR: None
- Latency p95 (ms): 22534.923957

#### leakage_exfiltration
- ASR: 0.625
- TPR: 0.375
- FPR: None
- Latency p95 (ms): 15949.066209

#### format_breaking_insecure_output
- ASR: 0.6666666666666666
- TPR: 0.3333333333333333
- FPR: None
- Latency p95 (ms): 13260.882143

#### multi_turn_escalation
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 40178.785031

#### data_exfiltration
- ASR: 0.7338129496402878
- TPR: 0.26618705035971224
- FPR: None
- Latency p95 (ms): 33881.909937

#### system_prompt_leak
- ASR: 0.7272727272727273
- TPR: 0.2727272727272727
- FPR: None
- Latency p95 (ms): 40160.336538

#### policy_override
- ASR: 0.6748466257668712
- TPR: 0.32515337423312884
- FPR: None
- Latency p95 (ms): 29865.442533

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.04108546791782906
- Latency p95 (ms): 34481.171943

## Utility metrics
- U mean (average utility_score): 0.44354665602647597
- Utility attempts scored: 9367 / 10000

### By task
#### SberQuAD
- U mean: 0.5271064715669757
- EM mean: 0.2641112047177759
- N: 4748

#### ruMMLU
- U mean: 0.3576531716821823
- N: 4619

