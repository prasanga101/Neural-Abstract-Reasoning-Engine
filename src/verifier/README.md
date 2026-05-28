# Verifier Module

This folder contains the post-execution validation layer. Its job is to decide whether the executed reasoning trace and the final environment state look valid enough to trust.

## Files

- [verifier.py](verifier.py): combines rule-based and model-based verification.
- [rule_checker.py](rule_checker.py): deterministic validation rules.
- [gemini_verifier.py](gemini_verifier.py): LLM-backed validation client.

## Verification strategy

The verifier is intentionally two-part:

### 1. Rule-based validation

[rule_checker.py](rule_checker.py) checks:

- no negative numeric values in environment state
- completed steps actually produced outputs
- required output keys are present for selected nodes
- expected environment keys were updated
- dependency-sensitive nodes did not run without prerequisite state

Examples of enforced dependency rules:

- route identification should not run without hospital and sensor context
- transport optimization should not run without alternative routes
- ambulance dispatch should not run without casualty estimates

### 2. LLM-based validation

[gemini_verifier.py](gemini_verifier.py) sends the following to the model client:

- the original scenario
- the execution trace
- the final environment state

It requests strict JSON in the form:

```json
{
  "valid": true,
  "reason": "explanation"
}
```

If the model call fails or returns malformed output, the verifier falls back to:

```json
{
  "valid": null,
  "reason": "Ollama verification unavailable: ..."
}
```

## Overall validity rule

[verifier.py](verifier.py) sets `overall_valid` to `true` only if:

- the rule checker returns `valid = true`
- the model-based verifier also returns `valid = true`

This makes the verifier conservative by design.

## Environment requirements

This module expects a local Ollama server. The default URL is `http://localhost:11434`.

You can optionally set:

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_VERIFIER_MODEL`

If omitted, the verifier defaults to `llama3.2`.

## Notes

- The current client code calls Ollama's local `/api/generate` endpoint and requests JSON output.
- The model verifier is useful for semantic judgment, while the rule checker guards against obvious structural errors.
