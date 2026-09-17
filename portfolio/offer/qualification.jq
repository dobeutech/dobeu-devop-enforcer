def contains_sensitive:
  [.workflow.data_classes[] | select(. == "applicant_pii" or . == "resume" or . == "employment" or . == "financial" or . == "health" or . == "credential" or . == "unknown")] | length > 0;

def points:
  (if .contact.business_email_present then 5 else 0 end)
  + (if .contact.process_owner then 15 else 0 end)
  + (if .workflow.weekly_volume >= 10 then 10 elif .workflow.weekly_volume > 0 then 5 else 0 end)
  + (if ((.workflow.weekly_volume * .workflow.operator_minutes_per_item * 4.33) / 60) >= 10 then 20 elif ((.workflow.weekly_volume * .workflow.operator_minutes_per_item * 4.33) / 60) >= 3 then 10 else 0 end)
  + (if (.workflow.wait_hours_per_item // 0) > 0 or (.workflow.rework_percent // 0) > 0 then 10 else 0 end)
  + (if .commercial.desired_start_days <= 30 then 15 elif .commercial.desired_start_days <= 90 then 8 else 0 end)
  + (if .commercial.diagnostic_budget_confirmed then 20 else 0 end)
  + (if .authorization.can_authorize_discovery and .authorization.terms_acknowledged then 5 else 0 end);

. as $lead
| (points) as $score
| ([
    if (.authorization.autonomous_employment_decision_requested) then "Autonomous employment decisions are outside the offer boundary." else empty end,
    if (.authorization.can_authorize_discovery | not) then "No authorized discovery owner is present." else empty end,
    if (.authorization.terms_acknowledged | not) then "Diagnostic terms are not acknowledged." else empty end
  ]) as $stops
| ([
    if contains_sensitive then "security_and_data_review" else empty end,
    if .authorization.production_access_requested then "explicit_production_access_approval" else empty end,
    if (.workflow.external_actions | length) > 0 then "external_action_approval" else empty end,
    "payment_before_delivery"
  ] | unique) as $gates
| {
    schema: "staffing-diagnostic-qualification/v1",
    intake_id: $lead.intake_id,
    score: $score,
    modeled_operator_hours_per_month: ((.workflow.weekly_volume * .workflow.operator_minutes_per_item * 4.33) / 60 * 100 | round / 100),
    disposition: (if ($stops | length) > 0 then "outside_current_boundary" elif $score >= 70 then "invite_to_scope_call" elif $score >= 45 then "manual_review" else "not_economic_now" end),
    stop_reasons: $stops,
    required_gates: $gates,
    note: "This deterministic triage prioritizes a scope conversation. It is not an employment decision, credit decision, or authorization to access systems or data."
  }
