class RuleChecker:
    def validate_execution(self, env, execution_trace):
        errors = []
        state = env.get_full_state()

        errors.extend(self._check_negative_values(state))
        errors.extend(self._check_required_outputs(state, execution_trace))
        errors.extend(self._check_dependency_rules(state, execution_trace))
        print("STATE:", state)
        print("TRACE:", execution_trace)

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _check_negative_values(self, state):
        errors = []

        for key, value in state.items():
            if isinstance(value, (int, float)) and value < 0:
                errors.append(f"{key} cannot be negative")

        return errors

    def _check_required_outputs(self, state, execution_trace):
        errors = []

        required_output_map = {
            "assess_injury_severity": "injury_severity",
            "estimate_number_of_casualties": "estimated_casualties",
            "dispatch_ambulances": "ambulances_dispatched",
            "allocate_temporary_shelters": "shelters_allocated",
            "collect_sensor_data": "sensor_data",
            "identify_nearest_hospitals": "nearby_hospitals",
            "identify_alternative_routes": "alternative_routes",
            "optimize_transport_paths": "optimized_route",
        }

        env_state_map = {
            "assess_injury_severity": "injury_severity",
            "estimate_number_of_casualties": "estimated_casualties",
            "collect_sensor_data": "sensor_data",
            "identify_nearest_hospitals": "nearby_hospitals",
            "identify_alternative_routes": "alternative_routes",
            "optimize_transport_paths": "optimized_route",
        }

        for step in execution_trace:
            node = step.get("node")
            status = step.get("status")

            if status == "completed":
                if "output" not in step or step["output"] is None:
                    errors.append(f"{node} completed but produced no output")
                    continue

                expected_output = required_output_map.get(node)
                if expected_output and expected_output not in step["output"]:
                    errors.append(f"{node} output missing expected key {expected_output}")

                expected_env_key = env_state_map.get(node)
                if expected_env_key and state.get(expected_env_key) is None:
                    errors.append(f"{node} did not update env key {expected_env_key}")
                    print("Checking node:", node)
            print("Step output:", step.get("output"))
            print("Expected env key:", expected_env_key)
            print("Env value:", state.get(expected_env_key))

        return errors

    def _check_dependency_rules(self, state, execution_trace):
        errors = []
        executed_nodes = {
            step.get("node")
            for step in execution_trace
            if step.get("status") == "completed"
        }

        if "identify_nearest_hospitals" in executed_nodes:
            if state.get("event_context") is None:
                errors.append("identify_nearest_hospitals ran without event_context")

        if "identify_alternative_routes" in executed_nodes:
            if not state.get("nearby_hospitals"):
                errors.append("identify_alternative_routes ran without nearby_hospitals")
            if state.get("sensor_data") is None:
                errors.append("identify_alternative_routes ran without sensor_data")

        if "optimize_transport_paths" in executed_nodes:
            if not state.get("alternative_routes"):
                errors.append("optimize_transport_paths ran without alternative_routes")

        if "dispatch_ambulances" in executed_nodes:
            if state.get("estimated_casualties") is None:
                errors.append("dispatch_ambulances ran without estimated_casualties")

        if "allocate_temporary_shelters" in executed_nodes:
            if state.get("estimated_casualties") is None:
                errors.append("allocate_temporary_shelters ran without estimated_casualties")

        return errors