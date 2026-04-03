#we define a very basic rule checker that validates the execution trace against some simple rules. In a real implementation, this would be much more complex and would likely involve checking for specific conditions based on the domain of the problem.
class RuleChecker:
    def validate_execution(self, env, execution_trace):
        errors = []

        state = env.get_full_state()

        for key, value in state.items():
            if isinstance(value, (int, float)) and value < 0:
                errors.append(f"{key} cannot be negative")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }