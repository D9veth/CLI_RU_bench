# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.9614285714285714
- TPR: 0.03857142857142857
- FPR: 0.02075
- Latency p50 (ms): 16535.751999996137
- Latency p95 (ms): 32055.726292004692

### By category
#### prompt_injection_jailbreak
- ASR: 0.9897435897435898
- TPR: 0.010256410256410256
- FPR: None
- Latency p95 (ms): 21420.12637500011

#### leakage_exfiltration
- ASR: 0.875
- TPR: 0.125
- FPR: None
- Latency p95 (ms): 16072.476457993616

#### format_breaking_insecure_output
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 13553.625208995072

#### multi_turn_escalation
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 32961.24554199923

#### data_exfiltration
- ASR: 0.9428571428571428
- TPR: 0.05714285714285714
- FPR: None
- Latency p95 (ms): 34713.381749999826

#### system_prompt_leak
- ASR: 0.9642857142857143
- TPR: 0.03571428571428571
- FPR: None
- Latency p95 (ms): 36388.886790999095

#### policy_override
- ASR: 0.9515151515151515
- TPR: 0.048484848484848485
- FPR: None
- Latency p95 (ms): 29720.058916995185

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.02075
- Latency p95 (ms): 31860.430625005392

## Utility metrics
- U mean (average utility_score): 0.49149832079154976
- Utility attempts scored: 9367 / 10000

### By task
#### SberQuAD
- U mean: 0.5469729541708893
- EM mean: 0.2252
- N: 5000

#### ruMMLU
- U mean: 0.4279825967483398
- N: 4367

