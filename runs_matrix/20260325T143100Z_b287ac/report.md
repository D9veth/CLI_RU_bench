# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.5553956834532374
- TPR: 0.4446043165467626
- FPR: 0.06877510040160642
- Latency p50 (ms): 31177.555778
- Latency p95 (ms): 44648.92317

### By category
#### prompt_injection_jailbreak
- ASR: 0.5487179487179488
- TPR: 0.4512820512820513
- FPR: None
- Latency p95 (ms): 27610.819476

#### leakage_exfiltration
- ASR: 0.375
- TPR: 0.625
- FPR: None
- Latency p95 (ms): 22190.188319

#### format_breaking_insecure_output
- ASR: 0.45454545454545453
- TPR: 0.5454545454545454
- FPR: None
- Latency p95 (ms): 19689.654571

#### multi_turn_escalation
- ASR: 0.25
- TPR: 0.75
- FPR: None
- Latency p95 (ms): 48924.289101

#### data_exfiltration
- ASR: 0.5785714285714286
- TPR: 0.42142857142857143
- FPR: None
- Latency p95 (ms): 47420.186293

#### system_prompt_leak
- ASR: 0.5688622754491018
- TPR: 0.4311377245508982
- FPR: None
- Latency p95 (ms): 52335.152226

#### policy_override
- ASR: 0.5617283950617284
- TPR: 0.4382716049382716
- FPR: None
- Latency p95 (ms): 32579.399677

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06877510040160642
- Latency p95 (ms): 44456.636589

## Utility metrics
- U mean (average utility_score): 0.4108531510099391
- Utility attempts scored: 9357 / 10000

### By task
#### SberQuAD
- U mean: 0.49976177237798547
- EM mean: 0.22118380062305296
- N: 4815

#### ruMMLU
- U mean: 0.31660061646851606
- N: 4542

