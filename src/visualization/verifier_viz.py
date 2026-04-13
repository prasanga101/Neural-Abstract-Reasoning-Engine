def build_verifier_viz(verification_result):
    return {
        "valid": verification_result["overall_valid"],
        "rule": verification_result["rule_validation"]["valid"],
        "gemini": verification_result["gemini_validation"]["valid"],
        "reason": verification_result["gemini_validation"]["reason"]
    }