package governance.static

# Static policy over workflow facts. Input shape (built by scripts/governance/govern.py):
#   input.policy   policy/policy.yml
#   input.waivers  policy/waivers.yml
#   input.today    evaluation date, ISO 8601 (passed in so evaluation is reproducible)
#   input.facts    files[], agentic[], pipeline

import rego.v1

violation(rule, subject, severity, message) := {
	"rule": rule,
	"subject": subject,
	"severity": severity,
	"message": message,
}

workflow_files := [f | some f in input.facts.files; startswith(f.file, ".github/workflows/")]

write_scopes(perms) := {s | some s, level in perms; level == "write"} if is_object(perms)

write_scopes(perms) := set() if not is_object(perms)

# ---- runners ---------------------------------------------------------------
violations contains v if {
	some f in input.facts.files
	some j in f.jobs
	not j.reusable
	j.runs_on != input.policy.runners.required
	v := violation("runner-pin", sprintf("%s#%s", [f.file, j.id]), "error",
		sprintf("job runs on %v; policy requires %s", [j.runs_on, input.policy.runners.required]))
}

violations contains v if {
	some a in input.facts.agentic
	some field, label in {
		"runs_on": "runs-on",
		"safe_outputs_runs_on": "safe-outputs.runs-on",
		"threat_detection_runs_on": "safe-outputs.threat-detection.runs-on",
	}
	object.get(a, field, null) != input.policy.runners.required
	v := violation("runner-pin", a.id, "error",
		sprintf("%s is %v; policy requires %s", [label, object.get(a, field, null), input.policy.runners.required]))
}

# ---- supply chain ----------------------------------------------------------
violations contains v if {
	input.policy.actions.require_sha_pin
	some f in input.facts.files
	some u in f.uses
	u.kind != "local"
	not u.pinned
	v := violation("action-pin", f.file, "error",
		sprintf("%s is not pinned to a commit SHA or image digest (job %s)", [u.ref, u.job]))
}

violations contains v if {
	some f in input.facts.files
	some u in f.uses
	u.kind == "action"
	not u.owner in input.policy.actions.allowed_owners
	v := violation("action-owner", f.file, "error",
		sprintf("%s comes from owner '%s', which is not in the approved list", [u.ref, u.owner]))
}

# ---- least privilege -------------------------------------------------------
violations contains v if {
	some f in workflow_files
	not f.permissions
	v := violation("permissions-declared", f.file, "error", "no top-level permissions block; declare `permissions: {}` and grant per job")
}

violations contains v if {
	some f in workflow_files
	f.permissions == "write-all"
	v := violation("permissions-declared", f.file, "error", "top-level permissions is write-all")
}

violations contains v if {
	some f in input.facts.files
	some j in f.jobs
	j.id in input.policy.permissions.read_only_jobs
	extra := write_scopes(j.permissions) - {s | some s in input.policy.permissions.write_allowed_for_read_only_jobs}
	count(extra) > 0
	v := violation("agent-job-read-only", sprintf("%s#%s", [f.file, j.id]), "error",
		sprintf("job holds write scopes %v; writes must go through safe outputs", [sort(extra)]))
}

violations contains v if {
	some a in input.facts.agentic
	extra := write_scopes(a.permissions) - {s | some s in input.policy.permissions.frontmatter_write_allowed}
	count(extra) > 0
	v := violation("frontmatter-write-permission", a.id, "error",
		sprintf("frontmatter requests write scopes %v", [sort(extra)]))
}

violations contains v if {
	some f in input.facts.files
	some t in f.triggers
	t in input.policy.triggers.forbidden
	v := violation("forbidden-trigger", f.file, "error", sprintf("trigger %s is forbidden", [t]))
}

# ---- agent definition ------------------------------------------------------
violations contains v if {
	some a in input.facts.agentic
	not a.engine in input.policy.engines.allowed
	v := violation("engine-allowlist", a.id, "error", sprintf("engine %v is not in %v", [a.engine, input.policy.engines.allowed]))
}

violations contains v if {
	some a in input.facts.agentic
	a.model != null
	not model_allowed(a.model)
	v := violation("model-allowlist", a.id, "error", sprintf("model %v is not allowed", [a.model]))
}

model_allowed(model) if {
	some pattern in input.policy.models.allowed
	glob.match(pattern, null, model)
	not model_denied(model)
}

model_denied(model) if {
	some pattern in input.policy.models.denied
	glob.match(pattern, null, model)
}

violations contains v if {
	some a in input.facts.agentic
	some entry in a.network.entries
	not entry in input.policy.network.allowed_entries
	v := violation("network-allowlist", a.id, "error", sprintf("network entry '%s' is not approved", [entry]))
}

violations contains v if {
	some a in input.facts.agentic
	input.policy.tools.forbid_unrestricted_bash
	a.bash.unrestricted
	v := violation("bash-restricted", a.id, "error", "bash tool is enabled without a command allowlist")
}

violations contains v if {
	some a in input.facts.agentic
	input.policy.safe_outputs.require_threat_detection
	not a.threat_detection_enabled
	v := violation("threat-detection-required", a.id, "error", "safe-outputs threat detection is disabled")
}

violations contains v if {
	some a in input.facts.agentic
	some type, cfg in a.safe_outputs
	not type in input.policy.safe_outputs.allowed_types
	v := violation("safe-output-type", a.id, "error", sprintf("safe output '%s' is not approved", [type]))
}

violations contains v if {
	some a in input.facts.agentic
	some type, cfg in a.safe_outputs
	cfg.max != null
	cfg.max > input.policy.safe_outputs.max_per_type
	v := violation("safe-output-max", a.id, "error",
		sprintf("safe output '%s' allows %v per run; ceiling is %v", [type, cfg.max, input.policy.safe_outputs.max_per_type]))
}

violations contains v if {
	some a in input.facts.agentic
	a.lock == null
	v := violation("lock-file-present", a.id, "error", "no compiled .lock.yml; run `gh aw compile`")
}

# ---- token and time budgets ------------------------------------------------
budget_for(id) := object.union(input.policy.budgets.default, object.get(input.policy.budgets.workflows, id, {}))

violations contains v if {
	some a in input.facts.agentic
	some field, label in {"max_ai_credits": "max-ai-credits", "max_daily_ai_credits": "max-daily-ai-credits"}
	object.get(a, field, null) == null
	v := violation("budget-missing", a.id, "error", sprintf("`%s` is not set to a number in the frontmatter", [label]))
}

violations contains v if {
	some a in input.facts.agentic
	some field, label in {"max_ai_credits": "max-ai-credits", "max_daily_ai_credits": "max-daily-ai-credits"}
	value := object.get(a, field, null)
	value != null
	value > budget_for(a.id)[field]
	v := violation("budget-exceeded", a.id, "error",
		sprintf("`%s` is %v; ceiling is %v", [label, value, budget_for(a.id)[field]]))
}

violations contains v if {
	some a in input.facts.agentic
	object.get(a, "timeout_minutes", null) == null
	v := violation("budget-missing", a.id, "error", "`timeout-minutes` is not set")
}

violations contains v if {
	some a in input.facts.agentic
	a.timeout_minutes != null
	a.timeout_minutes > budget_for(a.id).max_timeout_minutes
	v := violation("budget-exceeded", a.id, "error",
		sprintf("`timeout-minutes` is %v; ceiling is %v", [a.timeout_minutes, budget_for(a.id).max_timeout_minutes]))
}

# ---- repository pipeline gate ---------------------------------------------
violations contains v if {
	p := input.facts.pipeline
	not p.present
	v := violation("pipeline-gate", input.policy.pipeline_gate.file, "error", "pipeline workflow not found")
}

violations contains v if {
	p := input.facts.pipeline
	p.present
	not p.gate_present
	v := violation("pipeline-gate", p.file, "error", sprintf("job '%s' not found", [input.policy.pipeline_gate.job]))
}

violations contains v if {
	p := input.facts.pipeline
	p.gate_present
	not contains(p.gate_if, "always()")
	v := violation("pipeline-gate", p.file, "error", "gate job must run with `if: always()` so skipped stages cannot hide a failure")
}

violations contains v if {
	p := input.facts.pipeline
	p.gate_present
	some stage in p.jobs
	stage != input.policy.pipeline_gate.job
	not stage in p.gate_needs
	v := violation("pipeline-gate", p.file, "error", sprintf("stage '%s' is not required by the gate", [stage]))
}

violations contains v if {
	p := input.facts.pipeline
	p.gate_present
	some stage in input.policy.pipeline_gate.required_stages
	not stage in p.jobs
	v := violation("pipeline-gate", p.file, "error", sprintf("required stage '%s' is missing from the pipeline", [stage]))
}

# ---- waivers ---------------------------------------------------------------
waiver_problems(w) := [msg |
	some field in input.policy.waivers.required_fields
	not w[field]
	msg := sprintf("missing field '%s'", [field])
]

valid_expiry(w) if {
	is_string(w.expires)
	regex.match(`^\d{4}-\d{2}-\d{2}$`, w.expires)
}

waiver_active(w) if {
	count(waiver_problems(w)) == 0
	valid_expiry(w)
	w.expires >= input.today
	time.parse_ns("2006-01-02", w.expires) - time.parse_ns("2006-01-02", input.today) <= input.policy.waivers.max_days * 86400 * 1000000000
}

violations contains v if {
	some w in input.waivers
	problems := waiver_problems(w)
	count(problems) > 0
	v := violation("waiver-invalid", object.get(w, "id", "(no id)"), "error", sprintf("waiver is incomplete: %v", [problems]))
}

violations contains v if {
	some w in input.waivers
	count(waiver_problems(w)) == 0
	not valid_expiry(w)
	v := violation("waiver-invalid", w.id, "error", "expires must be an ISO date (YYYY-MM-DD)")
}

violations contains v if {
	some w in input.waivers
	count(waiver_problems(w)) == 0
	valid_expiry(w)
	w.expires < input.today
	v := violation("waiver-expired", w.id, "error", sprintf("waiver expired on %s; renew or remove it", [w.expires]))
}

violations contains v if {
	some w in input.waivers
	count(waiver_problems(w)) == 0
	valid_expiry(w)
	w.expires >= input.today
	not waiver_active(w)
	v := violation("waiver-invalid", w.id, "error",
		sprintf("waiver is valid for more than %v days", [input.policy.waivers.max_days]))
}

unused_waiver_warnings contains v if {
	some w in input.waivers
	waiver_active(w)
	not waiver_used(w)
	v := violation("waiver-unused", w.id, "warn", "waiver matches no current violation; remove it")
}

waiver_matches(w, v) if {
	w.rule == v.rule
	w.subject == v.subject
}

waiver_matches(w, v) if {
	w.rule == v.rule
	startswith(v.subject, concat("", [w.subject, "#"]))
}

# Waivers cannot silence the rules that police waivers themselves.
unwaivable := {"waiver-invalid", "waiver-expired", "waiver-unused"}

active_waiver_for(v) := w if {
	some w in input.waivers
	waiver_active(w)
	waiver_matches(w, v)
	not v.rule in unwaivable
}

waiver_used(w) if {
	some v in violations
	waiver_active(w)
	waiver_matches(w, v)
	not v.rule in unwaivable
}

waived_pairs := [{"violation": v, "waiver": w} |
	some v in violations
	v.severity == "error"
	some w in input.waivers
	waiver_active(w)
	waiver_matches(w, v)
	not v.rule in unwaivable
]

waived_set := {pair.violation | some pair in waived_pairs}

blocking := [v | some v in violations; v.severity == "error"; not v in waived_set]

warnings := array.concat([v | some v in violations; v.severity == "warn"], [v | some v in unused_waiver_warnings])

report := {
	"pass": count(blocking) == 0,
	"blocking": sort(blocking),
	"warnings": sort(warnings),
	"waived": sort(waived_pairs),
}
