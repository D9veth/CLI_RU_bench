# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.49928057553956834
- TPR: 0.5007194244604316
- FPR: 0.06831358709352155
- Latency p50 (ms): 29441.82422
- Latency p95 (ms): 42039.672792

### By category
#### prompt_injection_jailbreak
- ASR: 0.5284974093264249
- TPR: 0.47150259067357514
- FPR: None
- Latency p95 (ms): 26410.713097

#### leakage_exfiltration
- ASR: 0.4375
- TPR: 0.5625
- FPR: None
- Latency p95 (ms): 18618.457534

#### format_breaking_insecure_output
- ASR: 0.3333333333333333
- TPR: 0.6666666666666666
- FPR: None
- Latency p95 (ms): 14796.038795

#### multi_turn_escalation
- ASR: 0.25
- TPR: 0.75
- FPR: None
- Latency p95 (ms): 48095.663265

#### data_exfiltration
- ASR: 0.4892086330935252
- TPR: 0.5107913669064749
- FPR: None
- Latency p95 (ms): 42965.860659

#### system_prompt_leak
- ASR: 0.48502994011976047
- TPR: 0.5149700598802395
- FPR: None
- Latency p95 (ms): 49148.901511

#### policy_override
- ASR: 0.5121951219512195
- TPR: 0.4878048780487805
- FPR: None
- Latency p95 (ms): 34547.930533

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06831358709352155
- Latency p95 (ms): 41951.232077

## Utility metrics
- U mean (average utility_score): 0.41114595967308315
- Utility attempts scored: 9299 / 10000

### By task
#### SberQuAD
- U mean: 0.4976666554012026
- EM mean: 0.2351233671988389
- N: 4823

#### ruMMLU
- U mean: 0.31791778373547813
- N: 4476

