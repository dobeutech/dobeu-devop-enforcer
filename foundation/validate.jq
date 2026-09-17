def nonempty_string:
  type == "string" and length > 0;

def valid_sha256:
  type == "string" and test("^[a-f0-9]{64}$");

def unique_field($field):
  map(.[$field]) as $values
  | ($values | length) == ($values | unique | length);

def valid_source:
  .schema == "source-evidence/v1"
  and (.source_id | nonempty_string)
  and (.source_system | nonempty_string)
  and (.artifact_sha256 | valid_sha256)
  and (.status | IN("complete", "partial", "denied", "stale", "excluded", "conflict"))
  and (.allowed_actions | all(.[]; IN("read", "normalize", "validate", "report")))
  and (.coverage.processed_records >= 0)
  and (
    .coverage.expected_records == null
    or .coverage.processed_records <= .coverage.expected_records
  )
  and (.coverage.complete == (.status == "complete"))
  and (
    .status != "complete"
    or (
      .source_revision != null
      and .coverage.expected_records != null
      and .coverage.expected_records == .coverage.processed_records
      and .gap == null
    )
  )
  and (.status == "complete" or (.gap | nonempty_string));

def valid_connection:
  .schema == "connection/v1"
  and (.connection_id | nonempty_string)
  and (.provider | nonempty_string)
  and (.status | IN("ready", "partial", "denied", "conflict", "not_configured"))
  and (.allowed_actions | all(.[]; IN("read", "normalize", "validate", "report")))
  and (.evidence_refs | length > 0 and length == (unique | length))
  and (.status != "conflict" or (.failures | length > 0));

def valid_project:
  .schema == "project-mapping/v1"
  and (.project_id | nonempty_string)
  and (.project_alias | nonempty_string)
  and (.mapping_status | IN("mapped", "unmapped", "blocked"))
  and (
    .mapping_status != "mapped"
    or (
      (.repository_id | nonempty_string)
      and (.data_owner | nonempty_string)
      and .data_class != "unknown"
      and .backup_verified != null
    )
  );

def valid_memory:
  .schema == "memory-candidate/v1"
  and (.memory_id | nonempty_string)
  and (.artifact_sha256 | valid_sha256)
  and (.confidence >= 0 and .confidence <= 1)
  and .execution_authorized == false
  and (
    if .status == "accepted" then
      .indexed == true
      and (.reviewed_by | nonempty_string)
      and .contains_untrusted_instruction == false
    else
      .indexed == false
    end
  );

def valid_task:
  .schema == "task-envelope/v1"
  and (.task_id | nonempty_string)
  and (.objective | nonempty_string)
  and .external_writes_allowed == false
  and (.budget.max_workers >= 1 and .budget.max_workers <= 3)
  and (.success_criteria | length > 0)
  and (.stop_conditions | length > 0);

def valid_handoff:
  .schema == "agent-handoff/v1"
  and (.run_id | nonempty_string)
  and (.task_id | nonempty_string)
  and (.status | IN("complete", "partial", "blocked"))
  and (.coverage.processed >= 0)
  and (
    .coverage.expected == null
    or .coverage.processed <= .coverage.expected
  )
  and (
    if .status == "complete" then
      .coverage.complete == true and (.unknowns | length == 0)
    else
      .coverage.complete == false
    end
  );

def valid_usage:
  .schema == "usage-outcome/v1"
  and (.event_id | nonempty_string)
  and (.task_id | nonempty_string)
  and (.acceptance_status | IN("pending", "accepted", "rework", "rejected"))
  and (
    .input_tokens == null
    or .cached_input_tokens == null
    or .cached_input_tokens <= .input_tokens
  )
  and (
    .acceptance_status != "accepted"
    or (.artifact_ref | nonempty_string)
  );

def valid_approval:
  .schema == "approval/v1"
  and (.approval_id | nonempty_string)
  and (.action | nonempty_string)
  and (.status | IN("not_requested", "pending", "approved", "denied", "expired"))
  and (
    if .status == "approved" or .status == "denied" then
      (.decided_by | nonempty_string) and (.decided_at | nonempty_string)
    else
      .decided_by == null and .decided_at == null
    end
  );

def valid_revenue:
  .schema == "revenue-event/v1"
  and (.event_id | nonempty_string)
  and (.opportunity_id | nonempty_string)
  and (.amount_usd > 0)
  and (.kind | IN("payment", "refund"))
  and (.status | IN("pending", "settled", "failed", "refunded"))
  and (.status != "pending" or .collected_at == null);

def memory_fingerprints_unique:
  [.memory_candidates[] | [.source_uri, .source_revision, .source_locator] | join("|")]
  | length == (unique | length);

def references_are_known:
  ([.tasks[].task_id] | unique) as $tasks
  | ([.memory_candidates[].memory_id] | unique) as $memories
  | all(.handoffs[]; (.task_id as $id | $tasks | index($id) != null))
  and all(.usage_outcomes[]; (.task_id as $id | $tasks | index($id) != null))
  and all(.handoffs[].memory_candidate_ids[]; (. as $id | $memories | index($id) != null));

.schema == "internal-foundation/v1"
and (.snapshot_id | nonempty_string)
and .external_writes_allowed == false
and (.baseline_artifacts | unique_field("path"))
and all(.baseline_artifacts[]; (.path | nonempty_string) and (.sha256 | valid_sha256))
and (.sources | unique_field("source_id"))
and all(.sources[]; valid_source)
and (.connections | unique_field("connection_id"))
and all(.connections[]; valid_connection)
and (.projects | unique_field("project_id"))
and all(.projects[]; valid_project)
and (.memory_candidates | unique_field("memory_id"))
and all(.memory_candidates[]; valid_memory)
and memory_fingerprints_unique
and (.tasks | unique_field("task_id"))
and all(.tasks[]; valid_task)
and all(.handoffs[]; valid_handoff)
and (.usage_outcomes | unique_field("event_id"))
and all(.usage_outcomes[]; valid_usage)
and (.approvals | unique_field("approval_id"))
and all(.approvals[]; valid_approval)
and (.revenue_events | unique_field("event_id"))
and all(.revenue_events[]; valid_revenue)
and (.conflicts | unique_field("conflict_id"))
and all(.conflicts[]; (.evidence_refs | length >= 2 and length == (unique | length)))
and references_are_known
