package llm.guardrails

default allow := true

deny[msg] {
  input.stage == "input"
  contains(lower(input.text), "ignore previous")
  msg := "prompt injection marker"
}
