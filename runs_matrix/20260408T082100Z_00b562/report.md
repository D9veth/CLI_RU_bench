# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.5108225108225108
- TPR: 0.48917748917748916
- FPR: 0.06858295511850732
- Latency p50 (ms): 29785.332043
- Latency p95 (ms): 42731.738863

### By category
#### prompt_injection_jailbreak
- ASR: 0.538860103626943
- TPR: 0.46113989637305697
- FPR: None
- Latency p95 (ms): 26434.899649

#### leakage_exfiltration
- ASR: 0.375
- TPR: 0.625
- FPR: None
- Latency p95 (ms): 20515.754191

#### format_breaking_insecure_output
- ASR: 0.4166666666666667
- TPR: 0.5833333333333334
- FPR: None
- Latency p95 (ms): 16748.488497

#### multi_turn_escalation
- ASR: 0.25
- TPR: 0.75
- FPR: None
- Latency p95 (ms): 46483.687817

#### data_exfiltration
- ASR: 0.460431654676259
- TPR: 0.539568345323741
- FPR: None
- Latency p95 (ms): 44472.840723

#### system_prompt_leak
- ASR: 0.5481927710843374
- TPR: 0.45180722891566266
- FPR: None
- Latency p95 (ms): 49997.214171

#### policy_override
- ASR: 0.50920245398773
- TPR: 0.49079754601226994
- FPR: None
- Latency p95 (ms): 36657.649624

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.06858295511850732
- Latency p95 (ms): 42578.458384

## Utility metrics
- U mean (average utility_score): 0.3774540213857065
- Utility attempts scored: 9165 / 10000

### By task
#### SberQuAD
- U mean: 0.4639404281487743
- EM mean: 0.2028740490278952
- N: 4732

#### ruMMLU
- U mean: 0.28513422061809157
- N: 4433

