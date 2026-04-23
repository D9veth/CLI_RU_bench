# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.5512265512265512
- TPR: 0.44877344877344877
- FPR: 0.06980846774193548
- Latency p50 (ms): 28472.637613
- Latency p95 (ms): 40647.133839

### By category
#### prompt_injection_jailbreak
- ASR: 0.5794871794871795
- TPR: 0.4205128205128205
- FPR: None
- Latency p95 (ms): 25991.80175

#### leakage_exfiltration
- ASR: 0.375
- TPR: 0.625
- FPR: None
- Latency p95 (ms): 18696.237514

#### format_breaking_insecure_output
- ASR: 0.4166666666666667
- TPR: 0.5833333333333334
- FPR: None
- Latency p95 (ms): 14782.04225

#### multi_turn_escalation
- ASR: 0.5
- TPR: 0.5
- FPR: None
- Latency p95 (ms): 43328.79345

#### data_exfiltration
- ASR: 0.6546762589928058
- TPR: 0.34532374100719426
- FPR: None
- Latency p95 (ms): 43366.129631

#### system_prompt_leak
- ASR: 0.5060975609756098
- TPR: 0.49390243902439024
- FPR: None
- Latency p95 (ms): 46209.567067

#### policy_override
- ASR: 0.5030674846625767
- TPR: 0.49693251533742333
- FPR: None
- Latency p95 (ms): 34243.621562

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06980846774193548
- Latency p95 (ms): 40516.316452

## Utility metrics
- U mean (average utility_score): 0.415519260636012
- Utility attempts scored: 9308 / 10000

### By task
#### SberQuAD
- U mean: 0.4992020904376685
- EM mean: 0.22796100394109106
- N: 4821

#### ruMMLU
- U mean: 0.32560731000668597
- N: 4487

