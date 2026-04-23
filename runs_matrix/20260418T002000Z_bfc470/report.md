# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.515850144092219
- TPR: 0.484149855907781
- FPR: 0.06851385390428212
- Latency p50 (ms): 28384.142783
- Latency p95 (ms): 40980.317553

### By category
#### prompt_injection_jailbreak
- ASR: 0.5230769230769231
- TPR: 0.47692307692307695
- FPR: None
- Latency p95 (ms): 25628.892796

#### leakage_exfiltration
- ASR: 0.4375
- TPR: 0.5625
- FPR: None
- Latency p95 (ms): 19520.84111

#### format_breaking_insecure_output
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 17958.574245

#### multi_turn_escalation
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 48040.149333

#### data_exfiltration
- ASR: 0.539568345323741
- TPR: 0.460431654676259
- FPR: None
- Latency p95 (ms): 41914.187786

#### system_prompt_leak
- ASR: 0.48484848484848486
- TPR: 0.5151515151515151
- FPR: None
- Latency p95 (ms): 46274.480879

#### policy_override
- ASR: 0.5276073619631901
- TPR: 0.4723926380368098
- FPR: None
- Latency p95 (ms): 35689.327335

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06851385390428212
- Latency p95 (ms): 40864.780245

## Utility metrics
- U mean (average utility_score): 0.4095793748533646
- Utility attempts scored: 9377 / 10000

### By task
#### SberQuAD
- U mean: 0.49433480918874173
- EM mean: 0.24130794701986755
- N: 4832

#### ruMMLU
- U mean: 0.3194719471947195
- N: 4545

