# Bugfix Requirements Document

## Introduction

The Alternative Risk Supplier module in the supply chain risk analysis project has two critical bugs. First, every call to the recommendation endpoint produces different supplier rankings, risk scores, routes, costs, and delays — even when the underlying datasets have not changed. This is caused by random functions (`random.shuffle()`, `random.choice()`, `random.sample()`, and numpy/pandas random sampling) scattered through `routes/supplier_api.py`. Second, the route displayed after selecting an alternative supplier is either fabricated or unrelated to the chosen supplier, because routes are generated randomly rather than fetched from `route_dataset.csv`. Route cost and delay figures are similarly invented rather than derived from `cost_dataset.csv` and `delay_dataset.csv`. Both bugs undermine the module's usefulness as a decision-support tool.

---

## Bug Analysis

### Current Behavior (Defect)

**Bug 1 — Non-Deterministic Output**

1.1 WHEN the `/recommend` endpoint is called with the same `current_supplier_id` and the datasets have not changed, THEN the system returns a different alternative supplier ranking order on each call.

1.2 WHEN the scenario effects row is selected for risk calculation, THEN the system picks it with `scenario_df.sample(1)`, producing a randomly chosen row each time.

1.3 WHEN the live risk row cannot be matched by country, THEN the system falls back to `risk_df.sample(1)`, introducing a random risk score and risk level.

1.4 WHEN the alternative suppliers are scored, THEN the system may use randomly generated or shuffled intermediate values, so the final `ranking_score` differs across identical calls.

1.5 WHEN the top-ranked alternative is determined, THEN the resulting supplier name, country, risk score, cost, delay, and ranking list all vary between calls on the same input.

**Bug 2 — Incorrect Route Display**

1.6 WHEN an alternative supplier is recommended, THEN the system displays a transportation route that is not derived from `route_dataset.csv` for that supplier's origin.

1.7 WHEN the route cost is shown, THEN the system returns a randomly generated dollar figure rather than the total cost from `cost_dataset.csv` for the matching route.

1.8 WHEN the estimated delay is shown, THEN the system returns a randomly generated day count rather than the delay days from `delay_dataset.csv` for the matching route.

---

### Expected Behavior (Correct)

**Bug 1 — Deterministic Output**

2.1 WHEN the `/recommend` endpoint is called with the same `current_supplier_id` and the datasets have not changed, THEN the system SHALL return an identical alternative supplier ranking, risk score, route, cost, and delay on every call.

2.2 WHEN a scenario effects row is needed for risk calculation, THEN the system SHALL select it deterministically (e.g., by matching on supplier country or by using a fixed aggregation such as the mean of all rows for that country), not via random sampling.

2.3 WHEN the live risk row is matched by supplier country, THEN the system SHALL use the mean (or first sorted) risk score for that country derived from `live_risk_dataset.csv`, not a randomly chosen row.

2.4 WHEN alternative suppliers are scored, THEN the system SHALL calculate the ranking score exclusively from the dataset columns: geopolitical risk, sanctions exposure, oil price impact, reliability, shipping delay, supplier availability, distance, and historical performance — with no random components.

2.5 WHEN the top-ranked alternative is determined, THEN the system SHALL produce the same supplier name, country, risk score, cost, delay, and ranking list for the same input on every invocation.

**Bug 2 — Correct Route Display**

2.6 WHEN an alternative supplier is recommended, THEN the system SHALL display the complete transportation route from that supplier's source port to the current supplier's destination port, fetched from `route_dataset.csv`.

2.7 WHEN the route cost is shown, THEN the system SHALL return the `total_cost` value from `cost_dataset.csv` that corresponds to the matched route name, not a random value.

2.8 WHEN the estimated delay is shown, THEN the system SHALL return the `delay_days` value from `delay_dataset.csv` that corresponds to the matched route name, not a random value.

---

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a valid `current_supplier_id` is provided and the supplier is found in `current_supplier_dataset.csv`, THEN the system SHALL CONTINUE TO return a properly structured recommendation response including risk assessment, ranked alternatives, route, cost, and delay.

3.2 WHEN the risk assessment determines that no replacement is required (risk score ≤ 70, disruption probability ≤ 60%, shortage ≤ 30%, production loss ≤ 25%), THEN the system SHALL CONTINUE TO return a response indicating no replacement is needed without generating alternative rankings.

3.3 WHEN a `current_supplier_id` that does not exist in the dataset is provided, THEN the system SHALL CONTINUE TO return a 404 error response.

3.4 WHEN the request body is missing the `current_supplier_id` field, THEN the system SHALL CONTINUE TO return a 400 error response.

3.5 WHEN the `/current-suppliers` endpoint is called, THEN the system SHALL CONTINUE TO return the full list of current suppliers from `current_supplier_dataset.csv`.

3.6 WHEN alternative suppliers are ranked, THEN the system SHALL CONTINUE TO return at least the top ranked alternatives with their supplier name, country, and reasons for selection.

3.7 WHEN the route lookup finds no direct match in `route_dataset.csv` for the alternative supplier's source port and the current supplier's destination port, THEN the system SHALL CONTINUE TO handle the absence gracefully (e.g., return the closest available route or indicate no route found) without crashing.

---

## Bug Condition Derivation

### Bug 1 — Non-Deterministic Output

```pascal
FUNCTION isBugCondition_NonDeterministic(call1_result, call2_result)
  INPUT: two recommendation results for the same supplier_id with unchanged datasets
  OUTPUT: boolean

  RETURN call1_result.ranking != call2_result.ranking
      OR call1_result.risk_score != call2_result.risk_score
      OR call1_result.route != call2_result.route
END FUNCTION

// Property: Fix Checking
FOR ALL supplier_id IN current_supplier_dataset DO
  result_a ← recommend'(supplier_id)
  result_b ← recommend'(supplier_id)
  ASSERT result_a.ranking    = result_b.ranking
  ASSERT result_a.risk_score = result_b.risk_score
  ASSERT result_a.route      = result_b.route
  ASSERT result_a.cost       = result_b.cost
  ASSERT result_a.delay      = result_b.delay
END FOR

// Property: Preservation Checking
FOR ALL supplier_id WHERE NOT isBugCondition_NonDeterministic DO
  ASSERT F(supplier_id) = F'(supplier_id)
END FOR
```

### Bug 2 — Incorrect Route Display

```pascal
FUNCTION isBugCondition_WrongRoute(result, route_dataset)
  INPUT: recommendation result and route_dataset rows
  OUTPUT: boolean

  RETURN result.route NOT IN route_dataset
      OR result.cost  != lookup_cost(result.route, cost_dataset)
      OR result.delay != lookup_delay(result.route, delay_dataset)
END FUNCTION

// Property: Fix Checking
FOR ALL supplier_id WHERE replacement_required DO
  result ← recommend'(supplier_id)
  ASSERT result.route IN route_dataset
  ASSERT result.cost  = cost_dataset[result.route].total_cost
  ASSERT result.delay = delay_dataset[result.route].delay_days
END FOR

// Property: Preservation Checking
FOR ALL supplier_id WHERE NOT isBugCondition_WrongRoute DO
  ASSERT F(supplier_id).route  = F'(supplier_id).route
  ASSERT F(supplier_id).cost   = F'(supplier_id).cost
  ASSERT F(supplier_id).delay  = F'(supplier_id).delay
END FOR
```
