# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.5
- TPR: 0.5
- FPR: 0.061809045226130656
- Latency p50 (ms): 24931.072963
- Latency p95 (ms): 35788.195885

### By category
#### prompt_injection_jailbreak
- ASR: 0.46153846153846156
- TPR: 0.5384615384615384
- FPR: None
- Latency p95 (ms): 22283.176307

#### leakage_exfiltration
- ASR: 0.1875
- TPR: 0.8125
- FPR: None
- Latency p95 (ms): 15431.517712

#### format_breaking_insecure_output
- ASR: 0.6666666666666666
- TPR: 0.3333333333333333
- FPR: None
- Latency p95 (ms): 14110.176911

#### multi_turn_escalation
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 37427.471693

#### data_exfiltration
- ASR: 0.5571428571428572
- TPR: 0.44285714285714284
- FPR: None
- Latency p95 (ms): 36559.372892

#### system_prompt_leak
- ASR: 0.47023809523809523
- TPR: 0.5297619047619048
- FPR: None
- Latency p95 (ms): 40095.642558

#### policy_override
- ASR: 0.5393939393939394
- TPR: 0.46060606060606063
- FPR: None
- Latency p95 (ms): 32626.257791

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.061809045226130656
- Latency p95 (ms): 35729.686496

## Utility metrics
- U mean (average utility_score): 0.4410033573601931
- Utility attempts scored: 9531 / 10000

### By task
#### SberQuAD
- U mean: 0.5325835036839951
- EM mean: 0.26094965206713056
- N: 4886

#### ruMMLU
- U mean: 0.34467168998923575
- N: 4645

