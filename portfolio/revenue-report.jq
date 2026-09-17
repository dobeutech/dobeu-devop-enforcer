def sum_or_zero: add // 0;

($portfolio[0]) as $portfolio
| ($costs[0]) as $costs
| . as $ledger
| [
    $ledger.opportunities[] as $opportunity
    | $opportunity.payments[]?
    | . + {opportunity_id: $opportunity.opportunity_id, offer_id: $opportunity.offer_id}
  ] as $all_payments
| [
    $all_payments[]
    | select(
        .status == "settled"
        and .collected_at != null
        and (.evidence_reference // "" | length) > 0
        and .unaffiliated_customer == true
        and (.collected_at[0:10] >= $ledger.period_start)
        and (.collected_at[0:10] <= $ledger.period_end)
      )
  ] as $evidenced_settled
| ([$evidenced_settled[] | if .kind == "refund" then -.amount_usd else .amount_usd end] | sum_or_zero) as $collected
| ([
    $all_payments[]
    | select(.status == "settled" and ((.collected_at == null) or ((.evidence_reference // "" | length) == 0)))
  ] | length) as $settled_without_evidence
| ([
    $all_payments[]
    | select(.status == "settled" and .unaffiliated_customer != true)
  ] | length) as $settled_affiliated_or_unknown
| ([
    $ledger.opportunities[]
    | select(.stage != "closed_lost")
    | .proposed_amount_usd
    | select(. != null)
  ] | sum_or_zero) as $pipeline
| ([
    $ledger.opportunities[]
    | select(.stage != "closed_lost")
    | .contracted_amount_usd
    | select(. != null)
  ] | sum_or_zero) as $contracted
| ($portfolio.targets.annual_software_cost_usd) as $annual_cost
| ($portfolio.targets.minimum_collected_revenue_usd) as $minimum_goal
| ($portfolio.targets.operating_revenue_target_usd) as $operating_goal
| {
    schema: "revenue-control/v1",
    generated_at: $as_of,
    period: {start: $ledger.period_start, end: $ledger.period_end},
    cost_scope: $ledger.cost_scope,
    baseline_software_cost_usd: $annual_cost,
    minimum_collected_revenue_goal_usd: $minimum_goal,
    operating_collected_revenue_goal_usd: $operating_goal,
    collected_revenue_usd: $collected,
    contracted_not_collected_usd: (if $contracted > $collected then $contracted - $collected else 0 end),
    nominal_pipeline_usd: $pipeline,
    gap_to_exceed_cost_usd: (if $collected >= $minimum_goal then 0 else $minimum_goal - $collected end),
    gap_to_operating_goal_usd: (if $collected >= $operating_goal then 0 else $operating_goal - $collected end),
    revenue_exceeds_baseline_software_cost: ($collected > $annual_cost),
    operating_goal_met: ($collected >= $operating_goal),
    evidence: {
      opportunity_count: ($ledger.opportunities | length),
      evidenced_settled_payment_count: ($evidenced_settled | length),
      settled_payment_records_missing_evidence: $settled_without_evidence,
      settled_payment_records_affiliated_or_unknown: $settled_affiliated_or_unknown,
      duplicate_opportunity_ids: ([$ledger.opportunities[].opportunity_id] | group_by(.) | map(select(length > 1) | .[0])),
      duplicate_payment_ids: ([$all_payments[].payment_id] | group_by(.) | map(select(length > 1) | .[0])),
      stage_counts: ([$ledger.opportunities[] | .stage] | group_by(.) | map({stage: .[0], count: length}))
    },
    next_revenue_action: (
      if $collected == 0 then "Obtain approval to publish the diagnostic application and collect the first evidence-backed $750 diagnostic payment."
      elif $collected < $minimum_goal then "Advance the highest-fit paid opportunity while protecting delivery margin and payment evidence."
      elif $collected < $operating_goal then "The baseline software-cost goal is met; continue only profitable delivery toward the operating target."
      else "Operating target is met; verify all costs and payment evidence before declaring the one-year goal complete."
      end
    ),
    accounting_rule: "Only net settled payments from unaffiliated customers inside the goal period with a collection timestamp and durable evidence reference count as collected revenue. Pipeline and contracts are reported separately."
  }
