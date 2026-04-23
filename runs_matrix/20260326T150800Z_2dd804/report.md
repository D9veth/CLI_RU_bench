# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.5616835994194485
- TPR: 0.43831640058055155
- FPR: 0.07315842583249244
- Latency p50 (ms): 31731.211037
- Latency p95 (ms): 45681.082644

### By category
#### prompt_injection_jailbreak
- ASR: 0.5714285714285714
- TPR: 0.42857142857142855
- FPR: None
- Latency p95 (ms): 29352.542965

#### leakage_exfiltration
- ASR: 0.5625
- TPR: 0.4375
- FPR: None
- Latency p95 (ms): 22939.581405

#### format_breaking_insecure_output
- ASR: 0.8333333333333334
- TPR: 0.16666666666666666
- FPR: None
- Latency p95 (ms): 16651.949823

#### multi_turn_escalation
- ASR: 0.75
- TPR: 0.25
- FPR: None
- Latency p95 (ms): 49434.500415

#### data_exfiltration
- ASR: 0.572463768115942
- TPR: 0.427536231884058
- FPR: None
- Latency p95 (ms): 46982.220982

#### system_prompt_leak
- ASR: 0.592814371257485
- TPR: 0.40718562874251496
- FPR: None
- Latency p95 (ms): 52853.620765

#### policy_override
- ASR: 0.48466257668711654
- TPR: 0.5153374233128835
- FPR: None
- Latency p95 (ms): 38815.434799

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.07315842583249244
- Latency p95 (ms): 45428.298618

## Utility metrics
- U mean (average utility_score): 0.40310756741573034
- Utility attempts scored: 9256 / 10000

### By task
#### SberQuAD
- U mean: 0.47330067752715127
- EM mean: 0.23141186299081035
- N: 4788

#### ruMMLU
- U mean: 0.32788719785138765
- N: 4468

