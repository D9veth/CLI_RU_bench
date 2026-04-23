# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.7171717171717171
- TPR: 0.2828282828282828
- FPR: 0.04383075753737015
- Latency p50 (ms): 25763.402395
- Latency p95 (ms): 37014.378337

### By category
#### prompt_injection_jailbreak
- ASR: 0.6839378238341969
- TPR: 0.3160621761658031
- FPR: None
- Latency p95 (ms): 23752.404907

#### leakage_exfiltration
- ASR: 0.6875
- TPR: 0.3125
- FPR: None
- Latency p95 (ms): 13470.182462

#### format_breaking_insecure_output
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 13734.875157

#### multi_turn_escalation
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 42782.16872

#### data_exfiltration
- ASR: 0.7553956834532374
- TPR: 0.2446043165467626
- FPR: None
- Latency p95 (ms): 39522.498804

#### system_prompt_leak
- ASR: 0.7380952380952381
- TPR: 0.2619047619047619
- FPR: None
- Latency p95 (ms): 42596.430538

#### policy_override
- ASR: 0.7080745341614907
- TPR: 0.2919254658385093
- FPR: None
- Latency p95 (ms): 31585.421294

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.04383075753737015
- Latency p95 (ms): 36771.267679

## Utility metrics
- U mean (average utility_score): 0.4546519027911453
- Utility attempts scored: 9351 / 10000

### By task
#### SberQuAD
- U mean: 0.5424572032537502
- EM mean: 0.2708641453623495
- N: 4733

#### ruMMLU
- U mean: 0.364660025985275
- N: 4618

