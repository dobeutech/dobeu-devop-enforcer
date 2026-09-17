# Internal Foundation Control Plane

This directory is the first implementation slice from `spec.md` Section 31.9. It turns the existing public portfolio, cost, connector, launch, and revenue evidence into versioned contracts with deterministic validation and a consolidated readiness report.

It is intentionally local and read-only toward external systems. It does not reauthenticate a connector, inspect customer rows, run a Make scenario, deploy software, publish an offer, send outreach, modify billing, or change repository lifecycle state.

## Contracts

The eleven JSON Schemas in `schemas/` cover source evidence, connection capabilities, external-project mapping, governed memory candidates, bounded task envelopes, agent handoffs, token/outcome telemetry, approvals, revenue evidence, aggregate foundation state, and the readiness report. The JSON Schemas define portable shapes; `validate.jq` adds cross-record invariants such as unique IDs, evidence completeness, accepted-memory-only indexing, task reference integrity, and a hard prohibition on external writes in this slice.

`state.json` is the implementation-start snapshot. Its baseline artifacts are locked by SHA-256 so changed evidence cannot be silently treated as the approved baseline. Updating the snapshot is an explicit review action: refresh the source artifact, evaluate the change, update its evidence status, then replace the recorded hash and observation time together.

## Commands

Run the semantic, adversarial, baseline, and portfolio checks:

```bash
./foundation/validate.sh
```

Regenerate the deterministic JSON and Markdown readiness reports:

```bash
./foundation/report.sh
```

Prove that checked-in reports match the current inputs without changing files:

```bash
./foundation/report.sh --check
```

The same checks are exposed through `.ona/config.yaml`. There is no long-running service in this slice.

## Fixture coverage

`fixtures/edge-cases.json` covers:

- partial GitHub scope with an unknown company-wide total;
- contradictory Make observations;
- an unmapped Supabase project;
- accepted, rejected, and malicious-source memory candidates;
- explicit partial agent coverage;
- accepted and rejected usage outcomes;
- a pending approval boundary;
- verified settled, unverified settled, and pending revenue.

The validator also mutates that fixture in memory and proves that it rejects an external-write task, an indexed rejected memory, and duplicate source/revision/locator evidence.

## Next gate

`readiness.md` is the human handoff. It lists the exact evidence and approvals still needed. G1 through G7 remain closed; only G0, this bounded local implementation slice, is approved.
