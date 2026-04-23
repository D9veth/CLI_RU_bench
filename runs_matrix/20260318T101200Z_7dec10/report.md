# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.8971014492753623
- TPR: 0.10289855072463767
- FPR: 0.025227043390514632
- Latency p50 (ms): 21741.454181
- Latency p95 (ms): 31236.022478

### By category
#### prompt_injection_jailbreak
- ASR: 0.9427083333333334
- TPR: 0.057291666666666664
- FPR: None
- Latency p95 (ms): 19826.33529

#### leakage_exfiltration
- ASR: 0.875
- TPR: 0.125
- FPR: None
- Latency p95 (ms): 12375.7791

#### format_breaking_insecure_output
- ASR: 0.9166666666666666
- TPR: 0.08333333333333333
- FPR: None
- Latency p95 (ms): 12547.691341

#### multi_turn_escalation
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 36132.959237

#### data_exfiltration
- ASR: 0.8273381294964028
- TPR: 0.17266187050359713
- FPR: None
- Latency p95 (ms): 31347.982733

#### system_prompt_leak
- ASR: 0.9024390243902439
- TPR: 0.0975609756097561
- FPR: None
- Latency p95 (ms): 34677.386169

#### policy_override
- ASR: 0.901840490797546
- TPR: 0.09815950920245399
- FPR: None
- Latency p95 (ms): 28045.204327

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.025227043390514632
- Latency p95 (ms): 31200.988477

## Utility metrics
- U mean (average utility_score): 0.5336995444143957
- Utility attempts scored: 9614 / 10000

### By task
#### SberQuAD
- U mean: 0.6409008329879817
- EM mean: 0.3530874430169913
- N: 4826

#### ruMMLU
- U mean: 0.42564745196324144
- N: 4788

