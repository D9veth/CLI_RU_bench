# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.48345323741007196
- TPR: 0.516546762589928
- FPR: 0.07715582450832073
- Latency p50 (ms): 27080.119392
- Latency p95 (ms): 38633.132211

### By category
#### prompt_injection_jailbreak
- ASR: 0.46113989637305697
- TPR: 0.538860103626943
- FPR: None
- Latency p95 (ms): 25757.252018

#### leakage_exfiltration
- ASR: 0.4375
- TPR: 0.5625
- FPR: None
- Latency p95 (ms): 16431.893598

#### format_breaking_insecure_output
- ASR: 0.5833333333333334
- TPR: 0.4166666666666667
- FPR: None
- Latency p95 (ms): 15866.427235

#### multi_turn_escalation
- ASR: 0.25
- TPR: 0.75
- FPR: None
- Latency p95 (ms): 42489.075592

#### data_exfiltration
- ASR: 0.4714285714285714
- TPR: 0.5285714285714286
- FPR: None
- Latency p95 (ms): 41595.011007

#### system_prompt_leak
- ASR: 0.49101796407185627
- TPR: 0.5089820359281437
- FPR: None
- Latency p95 (ms): 44630.630341

#### policy_override
- ASR: 0.5153374233128835
- TPR: 0.48466257668711654
- FPR: None
- Latency p95 (ms): 34795.001661

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.07715582450832073
- Latency p95 (ms): 38340.942816

## Utility metrics
- U mean (average utility_score): 0.35709556270893994
- Utility attempts scored: 9273 / 10000

### By task
#### SberQuAD
- U mean: 0.43946599273557496
- EM mean: 0.20112079701120797
- N: 4818

#### ruMMLU
- U mean: 0.26801346801346804
- N: 4455

