def build_verifier_viz(verification_result):
    llm_result = verification_result.get("llm_validation") or verification_result["gemini_validation"]
    llm_valid = llm_result["valid"]
    return {
        "valid": verification_result["overall_valid"],
        "rule": verification_result["rule_validation"]["valid"],
        "llm": llm_valid,
        "gemini": llm_valid,
        "reason": llm_result["reason"]
    }
