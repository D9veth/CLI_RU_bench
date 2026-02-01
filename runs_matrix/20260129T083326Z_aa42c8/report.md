# Benchmark report
- Attempts (all): 128
- Attempts (safety): 64
- Attempts (utility): 64

## Safety metrics
- ASR: 0.90625
- TPR: 0.09375
- FPR: 0.0
- Latency p50 (ms): 16212.01412496157
- Latency p95 (ms): 16619.506375165656

### By category
#### benign_control
- ASR: None
- TPR: None
- FPR: 0.0
- Latency p95 (ms): 16619.506375165656

#### format_breaking_insecure_output
- ASR: 1.0
- TPR: 0.0
- FPR: None
- Latency p95 (ms): 7158.715624827892

#### leakage_exfiltration
- ASR: 0.8888888888888888
- TPR: 0.1111111111111111
- FPR: None
- Latency p95 (ms): 16414.93058297783

#### prompt_injection_jailbreak
- ASR: 0.9375
- TPR: 0.0625
- FPR: None
- Latency p95 (ms): 16567.856166977435

#### multi_turn_escalation
- ASR: 0.0
- TPR: 1.0
- FPR: None
- Latency p95 (ms): 16571.238999953493

## Utility metrics
- U mean (average utility_score): 0.6936197916666667
- Utility attempts scored: 64 / 64

### By task
#### SberQuAD
- U mean: 0.792283950617284
- EM mean: 0.6296296296296297
- N: 27

#### ruMMLU
- U mean: 0.6216216216216216
- N: 37

