package governance.runtime

# Runtime policy over one agentic run's evidence record. Input shape:
#   input.policy    policy/policy.yml
#   input.evidence  agent-run-evidence/v1 built by scripts/governance/govern.py

import rego.v1

flag(rule, severity, message) := {"rule": rule, "severity": severity, "message": message}

workflow_key := input.evidence.run.workflow

# Workflow ids are file stems; the run record carries the display name, so match either.
budget := object.union(input.policy.budgets.default, object.get(input.policy.budgets.workflows, id_guess, {}))

id_guess := lower(replace(workflow_key, " ", "-"))

flags contains f if {
	e := input.evidence.agent.engine
	e != null
	not e in input.policy.engines.allowed
	f := flag("engine-allowlist", "error", sprintf("engine %v is not approved", [e]))
}

flags contains f if {
	m := input.evidence.agent.resolved_model
	m != null
	not model_allowed(m)
	f := flag("model-allowlist", "error", sprintf("model %v resolved at run time is not approved", [m]))
}

model_allowed(m) if {
	some pattern in input.policy.models.allowed
	glob.match(pattern, null, m)
	not model_denied(m)
}

model_denied(m) if {
	some pattern in input.policy.models.denied
	glob.match(pattern, null, m)
}

flags contains f if {
	used := input.evidence.usage.ai_credits
	used != null
	used > budget.max_ai_credits
	f := flag("budget-exceeded", "error", sprintf("run consumed %v AIC; ceiling is %v", [used, budget.max_ai_credits]))
}

flags contains f if {
	some key in ["prompt_injection", "secret_leak", "malicious_patch"]
	input.evidence.threat_detection[key] == true
	f := flag("threat-detected", "error", sprintf("threat detection reported %s", [key]))
}

flags contains f if {
	some type, _ in input.evidence.safe_outputs.by_type
	not safe_output_allowed(type)
	f := flag("safe-output-type", "error", sprintf("safe output '%s' is not approved", [type]))
}

# Evidence uses underscore type names (create_issue); policy lists both spellings.
safe_output_allowed(type) if type in input.policy.safe_outputs.allowed_types

safe_output_allowed(type) if replace(type, "_", "-") in input.policy.safe_outputs.allowed_types

safe_output_allowed(type) if type in {"noop", "report_incomplete", "report_missing_data", "report_missing_tool"}

flags contains f if {
	blocked := input.evidence.firewall.blocked_requests
	blocked != null
	blocked > 0
	f := flag("firewall-blocked", "warn", sprintf("%v outbound requests were blocked by the firewall", [blocked]))
}

flags contains f if {
	some area, present in input.evidence.completeness
	not present
	area in {"aw_info", "usage"}
	f := flag("evidence-incomplete", "warn", sprintf("artifact data for '%s' was not available", [area]))
}

report := {
	"pass": count([f | some f in flags; f.severity == "error"]) == 0,
	"flags": sort([f | some f in flags]),
}
