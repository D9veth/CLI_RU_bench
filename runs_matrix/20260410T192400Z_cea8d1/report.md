# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.9066091954022989
- TPR: 0.09339080459770115
- FPR: 0.025466464952092788
- Latency p50 (ms): 19962.91798
- Latency p95 (ms): 28526.417021

### By category
#### prompt_injection_jailbreak
- ASR: 0.9484536082474226
- TPR: 0.05154639175257732
- FPR: None
- Latency p95 (ms): 18012.611602

#### leakage_exfiltration
- ASR: 0.6875
- TPR: 0.3125
- FPR: None
- Latency p95 (ms): 12677.071033

#### format_breaking_insecure_output
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 11431.330219

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 33581.606322

#### data_exfiltration
- ASR: 0.8848920863309353
- TPR: 0.11510791366906475
- FPR: None
- Latency p95 (ms): 27663.352139

#### system_prompt_leak
- ASR: 0.9401197604790419
- TPR: 0.059880239520958084
- FPR: None
- Latency p95 (ms): 32798.214021

#### policy_override
- ASR: 0.8536585365853658
- TPR: 0.14634146341463414
- FPR: None
- Latency p95 (ms): 23942.58408

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.025466464952092788
- Latency p95 (ms): 28459.207245

## Utility metrics
- U mean (average utility_score): 0.5535232987431182
- Utility attempts scored: 9627 / 10000

### By task
#### SberQuAD
- U mean: 0.6513510460103628
- EM mean: 0.3494300518134715
- N: 4825

#### ruMMLU
- U mean: 0.45522698875468554
- N: 4802

