# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.8290229885057471
- TPR: 0.17097701149425287
- FPR: 0.031754032258064516
- Latency p50 (ms): 19995.139184
- Latency p95 (ms): 28690.15166

### By category
#### prompt_injection_jailbreak
- ASR: 0.841025641025641
- TPR: 0.15897435897435896
- FPR: None
- Latency p95 (ms): 17981.005402

#### leakage_exfiltration
- ASR: 0.625
- TPR: 0.375
- FPR: None
- Latency p95 (ms): 13919.466744

#### format_breaking_insecure_output
- ASR: 0.9166666666666666
- TPR: 0.08333333333333333
- FPR: None
- Latency p95 (ms): 9563.798887

#### multi_turn_escalation
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 32138.321496

#### data_exfiltration
- ASR: 0.8129496402877698
- TPR: 0.18705035971223022
- FPR: None
- Latency p95 (ms): 28536.629536

#### system_prompt_leak
- ASR: 0.8433734939759037
- TPR: 0.1566265060240964
- FPR: None
- Latency p95 (ms): 32673.358809

#### policy_override
- ASR: 0.8292682926829268
- TPR: 0.17073170731707318
- FPR: None
- Latency p95 (ms): 22778.569787

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.031754032258064516
- Latency p95 (ms): 28638.314418

## Utility metrics
- U mean (average utility_score): 0.5526274649496313
- Utility attempts scored: 9629 / 10000

### By task
#### SberQuAD
- U mean: 0.6572355926613069
- EM mean: 0.3630179344465059
- N: 4851

#### ruMMLU
- U mean: 0.4464210966931771
- N: 4778

