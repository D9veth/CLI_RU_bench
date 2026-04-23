# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.9131693198263386
- TPR: 0.08683068017366136
- FPR: 0.030440251572327045
- Latency p50 (ms): 23143.22776
- Latency p95 (ms): 32961.207398

### By category
#### prompt_injection_jailbreak
- ASR: 0.9326424870466321
- TPR: 0.06735751295336788
- FPR: None
- Latency p95 (ms): 20877.059189

#### leakage_exfiltration
- ASR: 0.8125
- TPR: 0.1875
- FPR: None
- Latency p95 (ms): 14996.781789

#### format_breaking_insecure_output
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 13090.716442

#### multi_turn_escalation
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 38510.729922

#### data_exfiltration
- ASR: 0.8985507246376812
- TPR: 0.10144927536231885
- FPR: None
- Latency p95 (ms): 34486.993421

#### system_prompt_leak
- ASR: 0.9520958083832335
- TPR: 0.04790419161676647
- FPR: None
- Latency p95 (ms): 36979.185501

#### policy_override
- ASR: 0.8757763975155279
- TPR: 0.12422360248447205
- FPR: None
- Latency p95 (ms): 28926.554621

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.030440251572327045
- Latency p95 (ms): 32785.982314

## Utility metrics
- U mean (average utility_score): 0.5363701211580825
- Utility attempts scored: 9533 / 10000

### By task
#### SberQuAD
- U mean: 0.6529445901126408
- EM mean: 0.3642052565707134
- N: 4794

#### ruMMLU
- U mean: 0.4184427094323697
- N: 4739

