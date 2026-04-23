# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.7727930535455861
- TPR: 0.2272069464544139
- FPR: 0.03172205438066465
- Latency p50 (ms): 18691.919386
- Latency p95 (ms): 27034.790948

### By category
#### prompt_injection_jailbreak
- ASR: 0.7783505154639175
- TPR: 0.22164948453608246
- FPR: None
- Latency p95 (ms): 17581.787109

#### leakage_exfiltration
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 10143.247806

#### format_breaking_insecure_output
- ASR: 0.8333333333333334
- TPR: 0.16666666666666666
- FPR: None
- Latency p95 (ms): 10844.039456

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 29745.688809

#### data_exfiltration
- ASR: 0.7226277372262774
- TPR: 0.2773722627737226
- FPR: None
- Latency p95 (ms): 28195.251276

#### system_prompt_leak
- ASR: 0.7926829268292683
- TPR: 0.2073170731707317
- FPR: None
- Latency p95 (ms): 30676.498453

#### policy_override
- ASR: 0.7804878048780488
- TPR: 0.21951219512195122
- FPR: None
- Latency p95 (ms): 23733.456243

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.03172205438066465
- Latency p95 (ms): 26893.302875

## Utility metrics
- U mean (average utility_score): 0.5364264287196514
- Utility attempts scored: 9638 / 10000

### By task
#### SberQuAD
- U mean: 0.6388762998141648
- EM mean: 0.33367747264092507
- N: 4843

#### ruMMLU
- U mean: 0.4329509906152242
- N: 4795

