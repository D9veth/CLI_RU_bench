# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.8565279770444764
- TPR: 0.14347202295552366
- FPR: 0.03058645096056623
- Latency p50 (ms): 22523.976914
- Latency p95 (ms): 32274.183081

### By category
#### prompt_injection_jailbreak
- ASR: 0.8871794871794871
- TPR: 0.11282051282051282
- FPR: None
- Latency p95 (ms): 20347.984506

#### leakage_exfiltration
- ASR: 0.875
- TPR: 0.125
- FPR: None
- Latency p95 (ms): 15060.869409

#### format_breaking_insecure_output
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 12554.255236

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 36907.908982

#### data_exfiltration
- ASR: 0.8357142857142857
- TPR: 0.16428571428571428
- FPR: None
- Latency p95 (ms): 35344.93579

#### system_prompt_leak
- ASR: 0.8383233532934131
- TPR: 0.16167664670658682
- FPR: None
- Latency p95 (ms): 37374.73979

#### policy_override
- ASR: 0.8404907975460123
- TPR: 0.15950920245398773
- FPR: None
- Latency p95 (ms): 25749.455528

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.03058645096056623
- Latency p95 (ms): 32130.382132

## Utility metrics
- U mean (average utility_score): 0.4790456089108911
- Utility attempts scored: 9494 / 10000

### By task
#### SberQuAD
- U mean: 0.5707809766904661
- EM mean: 0.2824443511129777
- N: 4762

#### ruMMLU
- U mean: 0.3867286559594252
- N: 4732

