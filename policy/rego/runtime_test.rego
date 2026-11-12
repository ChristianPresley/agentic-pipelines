package governance.runtime_test

import rego.v1

import data.governance.runtime

policy := {
	"engines": {"allowed": ["copilot"]},
	"models": {"allowed": ["claude-*", "auto"], "denied": []},
	"safe_outputs": {"allowed_types": ["add_comment"]},
	"budgets": {"default": {"max_ai_credits": 100}, "workflows": {}},
}

evidence := {
	"run": {"workflow": "Some Workflow"},
	"agent": {"engine": "copilot", "resolved_model": "claude-sonnet-5.5"},
	"usage": {"ai_credits": 50},
	"threat_detection": {"prompt_injection": false, "secret_leak": false, "malicious_patch": false},
	"safe_outputs": {"by_type": {"add_comment": 1}},
	"firewall": {"blocked_requests": 0},
	"completeness": {"aw_info": true, "usage": true},
}

errors(ev) := {f.rule | some f in runtime.report.flags with input as {"policy": policy, "evidence": ev}; f.severity == "error"}

test_clean_run_passes if {
	runtime.report.pass with input as {"policy": policy, "evidence": evidence}
}

test_over_budget if {
	"budget-exceeded" in errors(object.union(evidence, {"usage": {"ai_credits": 101}}))
}

test_unapproved_model if {
	"model-allowlist" in errors(object.union(evidence, {"agent": {"engine": "copilot", "resolved_model": "other-1"}}))
}

test_threat_detected if {
	"threat-detected" in errors(object.union(evidence, {"threat_detection": {"secret_leak": true}}))
}

test_unapproved_safe_output if {
	"safe-output-type" in errors(object.union(evidence, {"safe_outputs": {"by_type": {"create_issue": 1}}}))
}
