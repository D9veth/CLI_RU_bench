# Benchmark report
- Attempts (all): 14700
- Attempts (safety): 4700
- Attempts (utility): 10000

## Safety metrics
- ASR: 0.896700143472023
- TPR: 0.10329985652797705
- FPR: 0.023413897280966767
- Latency p50 (ms): 17493.176932
- Latency p95 (ms): 24962.447027

### By category
#### prompt_injection_jailbreak
- ASR: 0.9329896907216495
- TPR: 0.06701030927835051
- FPR: None
- Latency p95 (ms): 14316.030101

#### leakage_exfiltration
- ASR: 0.5625
- TPR: 0.4375
- FPR: None
- Latency p95 (ms): 11718.047868

#### format_breaking_insecure_output
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 9470.309011

#### multi_turn_escalation
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 27410.410676

#### data_exfiltration
- ASR: 0.8642857142857143
- TPR: 0.1357142857142857
- FPR: None
- Latency p95 (ms): 26261.792258

#### system_prompt_leak
- ASR: 0.9221556886227545
- TPR: 0.07784431137724551
- FPR: None
- Latency p95 (ms): 27882.312067

#### policy_override
- ASR: 0.8780487804878049
- TPR: 0.12195121951219512
- FPR: None
- Latency p95 (ms): 20320.384269

#### benign_control
- ASR: None
- TPR: None
- FPR: 0.023413897280966767
- Latency p95 (ms): 24918.247923

## Utility metrics
- U mean (average utility_score): 0.5805672406814661
- Utility attempts scored: 9685 / 10000

### By task
#### SberQuAD
- U mean: 0.6905562077761778
- EM mean: 0.3556881300144003
- N: 4861

#### ruMMLU
- U mean: 0.4697346600331675
- N: 4824

