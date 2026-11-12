package governance.static_test

import rego.v1

import data.governance.static

policy := {
	"runners": {"required": "ubuntu-26.04"},
	"engines": {"allowed": ["copilot"]},
	"models": {"allowed": ["claude-*"], "denied": []},
	"actions": {"require_sha_pin": true, "allowed_owners": ["actions"]},
	"permissions": {
		"read_only_jobs": ["agent"],
		"write_allowed_for_read_only_jobs": ["copilot-requests"],
		"frontmatter_write_allowed": ["copilot-requests"],
	},
	"triggers": {"forbidden": ["pull_request_target"]},
	"network": {"allowed_entries": ["defaults"]},
	"tools": {"forbid_unrestricted_bash": true},
	"safe_outputs": {"allowed_types": ["add_comment"], "max_per_type": 2, "require_threat_detection": true},
	"budgets": {"default": {"max_ai_credits": 100, "max_daily_ai_credits": 500, "max_timeout_minutes": 20}, "workflows": {}},
	"pipeline_gate": {"file": "p.yml", "job": "gate", "required_stages": []},
	"waivers": {"max_days": 90, "required_fields": ["id", "rule", "subject", "reason", "approved_by", "ticket", "expires"]},
}

good_agent := {
	"id": "a", "engine": "copilot", "model": null, "runs_on": "ubuntu-26.04",
	"safe_outputs_runs_on": "ubuntu-26.04", "threat_detection_runs_on": "ubuntu-26.04",
	"threat_detection_enabled": true, "permissions": {"contents": "read"},
	"network": {"entries": ["defaults"]}, "bash": {"unrestricted": false},
	"safe_outputs": {"add_comment": {"max": 1}}, "lock": "a.lock.yml",
	"max_ai_credits": 100, "max_daily_ai_credits": 500, "timeout_minutes": 20,
}

good_pipeline := {"present": true, "file": "p.yml", "gate_present": true, "gate_if": "${{ always() }}", "gate_needs": ["build"], "jobs": ["build", "gate"]}

make_input(agent, waivers) := {
	"policy": policy,
	"waivers": waivers,
	"today": "2026-01-01",
	"facts": {"files": [], "agentic": [agent], "pipeline": good_pipeline},
}

rules(inp) := {v.rule | some v in static.report.blocking with input as inp}

test_clean_input_passes if {
	static.report.pass with input as make_input(good_agent, [])
}

test_engine_denied if {
	"engine-allowlist" in rules(make_input(object.union(good_agent, {"engine": "other"}), []))
}

test_budget_exceeded if {
	"budget-exceeded" in rules(make_input(object.union(good_agent, {"max_ai_credits": 101}), []))
}

test_budget_missing if {
	"budget-missing" in rules(make_input(object.union(good_agent, {"max_ai_credits": null}), []))
}

test_runner_pin_on_safe_outputs if {
	"runner-pin" in rules(make_input(object.union(good_agent, {"safe_outputs_runs_on": "ubuntu-latest"}), []))
}

test_unapproved_safe_output if {
	"safe-output-type" in rules(make_input(object.union(good_agent, {"safe_outputs": {"create_issue": {"max": 1}}}), []))
}

test_gate_missing_stage if {
	inp := object.union(make_input(good_agent, []), {"facts": {"files": [], "agentic": [good_agent], "pipeline": object.union(good_pipeline, {"jobs": ["build", "extra", "gate"]})}})
	"pipeline-gate" in rules(inp)
}

waiver := {
	"id": "W1", "rule": "budget-exceeded", "subject": "a", "reason": "r",
	"approved_by": "owners", "ticket": "t", "expires": "2026-02-01",
}

over := object.union(good_agent, {"max_ai_credits": 101})

test_active_waiver_moves_violation if {
	inp := make_input(over, [waiver])
	static.report.pass with input as inp
	count(static.report.waived) == 1 with input as inp
}

test_expired_waiver_blocks if {
	inp := make_input(over, [object.union(waiver, {"expires": "2025-12-31"})])
	not static.report.pass with input as inp
	"waiver-expired" in rules(inp)
}

test_overlong_waiver_blocks if {
	inp := make_input(over, [object.union(waiver, {"expires": "2027-01-01"})])
	"waiver-invalid" in rules(inp)
}

test_unused_waiver_warns if {
	count(static.report.warnings) == 1 with input as make_input(good_agent, [waiver])
}
