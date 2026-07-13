# Alternative Supplier Fix — Bugfix Design

## Overview

The Alternative Risk Supplier module (`routes/supplier_api.py`, `utils/route_optimizer.py`,
`utils/preprocessing.py`) contains two bugs:

- **Bug 1 – Non-Deterministic Output**: Random functions (`random.shuffle`, `random.choice`,
  `random.sample`, `pandas.DataFrame.sample`) are used to select scenario-effect rows and live-risk
  rows, and possibly to shuffle ranking inputs. This means every call to `/recommend` with the same
  `current_supplier_id` can return a different ranking, risk score, route, cost, and delay.

- **Bug 2 – Incorrect Route / Cost / Delay**: After selecting the top-ranked alternative, the route
  displayed (including cost and delay) is either fabricated or taken from an unrelated random sample
  rather than being looked up in `route_dataset.csv`, `cost_dataset.csv`, and `delay_dataset.csv`
  against the alternative supplier's source port → current supplier's destination port.

The fix strategy:
1. Replace every random selection with a deterministic equivalent (mean aggregation over a country
   group, or sorted-first-row selection).
2. Compute `risk_score` exclusively from the eight dataset columns listed in the requirements.
3. Fetch route, cost, and delay from the appropriate CSV files by matching source country/port to
   destination port.

---

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — when the same `current_supplier_id`
  produces different outputs across calls, or when displayed route/cost/delay values are not derived
  from the CSV datasets.
- **Property (P)**: The desired behavior once fixed — identical outputs for identical inputs,
  route/cost/delay sourced from CSV lookups.
- **Preservation**: All non-random, dataset-driven behaviour (error responses, risk threshold logic,
  ranking model, existing API structure) must remain unchanged.
- **`recommend_suppliers`**: The Flask route handler in `routes/supplier_api.py` that performs the
  risk assessment and supplier ranking.
- **`risk_score`**: The numerical risk score derived deterministically from `live_risk_dataset.csv`
  columns (`geopolitical_risk`, `sanctions`, `oil_price_impact`, `reliability`, `shipping_delay`,
  `supplier_availability`, `distance`, `historical_performance`) via mean aggregation per country.
- **`RouteOptimizer`**: The class in `utils/route_optimizer.py` that builds a graph from
  `route_dataset.csv` and provides `find_best_route(source, target)`.

---

## Bug Details

### Bug Condition

**Bug 1** manifests whenever the endpoint selects scenario effects or live risk data using
`pandas.DataFrame.sample()` or any `random.*` call. Because the random seed is never fixed, every
call draws a different row, producing a different `risk_score`, `supply_shortage`,
`production_loss`, `cost_impact`, and ultimately a different ranking.

**Bug 2** manifests when the endpoint constructs route, cost, or delay output without querying the
CSV files for the specific alternative supplier. Instead it either returns None/empty or uses a
random route name / random numeric value.

**Formal Specification:**

```
FUNCTION isBugCondition(call_a_result, call_b_result)
  INPUT: two results for the same supplier_id, same datasets
  OUTPUT: boolean

  RETURN call_a_result.ranking    != call_b_result.ranking
      OR call_a_result.risk_score != call_b_result.risk_score
      OR call_a_result.route      != call_b_result.route
      OR call_a_result.cost       != call_b_result.cost
      OR call_a_result.delay      != call_b_result.delay
END FUNCTION
```

### Examples

- Calling `/recommend` with `{"current_supplier_id": "CUR_064"}` twice returns `ALT_043` ranked
  first on one call and `ALT_017` on the next — **should always return the same top-4 list**.
- The displayed route after recommendation shows "Route_37 (random)" — **should show the route from
  `route_dataset.csv` matching the alternative's source port to the current supplier's destination**.
- Cost displayed as `$1,234,567 (generated)` — **should be the `total_cost` from `cost_dataset.csv`
  for the matched route name**.
- Delay displayed as `7 days (random)` — **should be the mean `delay_days` from `delay_dataset.csv`
  for the matched route name**.

---

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The `/current-suppliers` GET endpoint continues to return the full `current_supplier_dataset.csv`
  list unchanged.
- The 400 response for a missing `current_supplier_id` field continues to be returned.
- The 404 response for an unknown `current_supplier_id` continues to be returned.
- When risk assessment concludes no replacement is needed, the response returns early without
  generating alternatives — this logic is unchanged.
- The `preprocess_supplier_data` function in `utils/preprocessing.py` is not modified.
- The Flask Blueprint registration and all existing route paths remain unchanged.
- The supplier ranking model (`models/supplier_ranker.pkl`) continues to be used for scoring.

**Scope:**
All logic that does NOT involve random sampling or route/cost/delay lookup should be completely
unaffected. This includes:
- Risk threshold comparisons (`risk_score > 70`, `prob_val > 0.60`, etc.)
- The LabelEncoder-based availability preprocessing
- The `RouteOptimizer` Dijkstra graph logic (structure unchanged; only the lookup call is wired in)

---

## Hypothesized Root Cause

1. **`scenario_df.sample(1)`** — Line in `recommend_suppliers` picks a random scenario row.
   Fix: Compute the mean of numeric columns across all rows in `scenario_effects_dataset.csv`
   (or group by the closest scenario type). Since the dataset has no country column to join on, we
   use the **global mean** of `supply_shortage`, `production_loss`, and `cost_impact`.

2. **`risk_df.sample(1)` fallback** — When no country match is found in `live_risk_dataset.csv`,
   a random row is used. Fix: Fall back to the **global mean** of numeric risk columns instead.

3. **`risk_score` sourced from `live_risk_dataset.csv`** — The column `risk_score` is already in
   the live risk dataset, so no derivation from individual columns is needed. However, because
   multiple rows exist per country, the mean must be taken. The `risk_level` and
   `disruption_probability` are also resolved by taking the mode (most-frequent value) per country.

4. **Route/cost/delay not looked up** — No code in `supplier_api.py` queries `route_dataset.csv`,
   `cost_dataset.csv`, or `delay_dataset.csv` after ranking. The `RouteOptimizer.find_best_route`
   method exists but is never called from the supplier API. Fix: After ranking, call
   `RouteOptimizer.find_best_route(alt_source_port, current_dest_port)` and look up the route name
   in `cost_dataset.csv` and `delay_dataset.csv`.

5. **Port information not in alternative_supplier_dataset.csv** — The dataset has `country` but not
   `source_port`. Fix: Derive the source port from `route_dataset.csv` by looking up the most
   common `source_port` for the alternative supplier's country (or the one with the smallest
   average distance as a tiebreaker). For the current supplier's destination port, similarly derive
   from `route_dataset.csv` using the current supplier's country.

---

## Correctness Properties

Property 1: Bug Condition — Deterministic Recommendation Output

_For any_ `current_supplier_id` where the datasets are unchanged, calling the fixed
`recommend_suppliers` endpoint twice SHALL return identical values for: alternative supplier
ranking order, risk score, risk level, disruption probability, supply shortage percentage,
production loss percentage, route name, route cost, and estimated delay.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Bug Condition — Dataset-Derived Route, Cost, and Delay

_For any_ `current_supplier_id` where a replacement is required, the fixed endpoint SHALL return a
`route` value that exists in `route_dataset.csv` connecting the alternative supplier's source port
to the current supplier's destination port, a `cost` equal to the mean `total_cost` from
`cost_dataset.csv` for that route name, and a `delay` equal to the mean `delay_days` from
`delay_dataset.csv` for that route name.

**Validates: Requirements 2.6, 2.7, 2.8**

Property 3: Preservation — Non-Random Behavior Unchanged

_For any_ input where the bug condition does NOT hold (i.e., inputs that never relied on random
sampling), the fixed endpoint SHALL produce the same result as the original endpoint, preserving
error responses, risk threshold logic, ranking model usage, and API structure.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

---

## Fix Implementation

### Changes Required

#### File: `routes/supplier_api.py`

**Function: `recommend_suppliers`**

**Specific Changes:**

1. **Remove `import random`** — The `random` module is no longer needed.

2. **Replace `scenario_df.sample(1).iloc[0]`** with the global mean of numeric columns:
   ```python
   scen_info = scenario_df[['supply_shortage', 'production_loss', 'cost_impact']].mean()
   ```
   This produces a deterministic Series with the same column names the rest of the code expects.

3. **Replace `risk_df.sample(1)` fallback** with a mean-aggregated fallback:
   ```python
   risk_info = risk_df[risk_df['supplier_country'] == supp_info['country']]
   if risk_info.empty:
       risk_info = risk_df[['risk_score']].mean()
       risk_level = 'Medium Risk'
       disruption_probability = 'Medium'
   else:
       risk_info_agg = risk_info.groupby('supplier_country', as_index=False).agg({
           'risk_score': 'mean',
           'risk_level': lambda x: x.mode()[0],
           'disruption_probability': lambda x: x.mode()[0]
       })
       risk_info = risk_info_agg.iloc[0]
   ```

4. **Add route/cost/delay lookup after ranking:**
   - Load `cost_dataset.csv` and `delay_dataset.csv` once at module level (alongside other datasets).
   - Load `route_dataset.csv` at module level (the `RouteOptimizer` also reads it, but for the port
     lookup we need the raw DataFrame).
   - For each top-ranked alternative, determine the alternative's typical `source_port` by finding
     the most frequent `source_port` for that supplier's country in `route_dataset.csv`.
   - Determine the current supplier's `destination_port` by finding the most frequent
     `destination_port` for the current supplier's country in `route_dataset.csv`.
   - Call `RouteOptimizer.find_best_route(source_port, dest_port)` to get the path and distance.
   - Extract the route name from the path (use `"Route_<node1>_to_<node2>"` naming, or match by
     the source/dest pair in `route_dataset.csv` to get the supplier name prefix, then look up cost
     and delay by route name pattern).

   Because `cost_dataset.csv` and `delay_dataset.csv` use route names like `Route_N` (not
   port-pair names), and `route_dataset.csv` uses supplier names, the practical lookup is:
   - Find rows in `route_dataset.csv` where `source_port == alt_source_port` AND
     `destination_port == curr_dest_port`.
   - Take the row with minimum `distance_km` (deterministic tiebreaker).
   - Extract `distance_km` and `expected_transit_days` directly from that row for display.
   - For cost: find the row in `cost_dataset.csv` where `distance_km` is closest to the matched
     route's distance (since cost rows also have `distance_km`). Use mean `total_cost` over all
     `cost_dataset.csv` rows matching within ±500 km, or simply use the global mean as a fallback.

   **Simpler deterministic approach** (avoids the N:M join problem):
   - Use the `RouteOptimizer` `find_best_route` for `distance_km` and `expected_transit_days`.
   - For cost: compute mean `total_cost` from `cost_dataset.csv` where
     `|distance_km - route_distance| <= tolerance` (tolerance = 2000 km), else global mean.
   - For delay: compute mean `delay_days` from `delay_dataset.csv` where
     `|distance_km - route_distance| <= tolerance`, else global mean.

5. **Add route information to the alternative entry** in the response:
   ```python
   {
       "rank": i,
       "supplier_id": ...,
       "supplier_name": ...,
       "country": ...,
       "ranking_score": ...,
       "Reason": ...,
       "Route": {
           "source_port": alt_source_port,
           "destination_port": curr_dest_port,
           "distance_km": route_distance,
           "expected_transit_days": route_days,
           "estimated_cost_usd": route_cost,
           "estimated_delay_days": route_delay
       }
   }
   ```

#### File: `utils/route_optimizer.py`

No structural changes needed. The `find_best_route` method already provides deterministic
Dijkstra-based routing. The only fix is to ensure it is actually called from `supplier_api.py`.

#### File: `utils/preprocessing.py`

No changes needed.

---

## Testing Strategy

### Validation Approach

Testing follows a two-phase approach: first confirm the bug is reproducible on the unfixed code
(exploratory), then verify the fix satisfies both determinism and correct dataset lookups.

### Exploratory Bug Condition Checking

**Goal**: Confirm that calling `/recommend` twice with the same input returns different results on
unfixed code, and that route/cost/delay values are not present or are random.

**Test Plan**: Call the endpoint programmatically twice with the same `current_supplier_id` and
assert that the results differ (expected to fail on fixed code, expected to pass on unfixed code).

**Test Cases:**
1. **Determinism test (Bug 1)**: Call `/recommend` with `CUR_064` twice; assert
   `result_a["Top 4 Ranked Suppliers"] != result_b["Top 4 Ranked Suppliers"]`.
   *(Will fail on unfixed code — results are random)*
2. **Risk score test (Bug 1)**: Call `/recommend` with `CUR_064` twice; assert
   `result_a["Risk Assessment"]["Risk Score"] != result_b["Risk Assessment"]["Risk Score"]`.
3. **Route presence test (Bug 2)**: Assert that each alternative in the response contains a `Route`
   key with `source_port`, `destination_port`, `distance_km`, `estimated_cost_usd`.
   *(Will fail on unfixed code — key absent)*
4. **Route dataset validity test (Bug 2)**: Assert that `source_port` and `destination_port` in the
   response are values that appear in `route_dataset.csv`.

**Expected Counterexamples:**
- Rankings differ between calls because `scen_info` is a different random scenario row.
- `Route` key is absent or contains `None` because no dataset lookup was implemented.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces
deterministic, dataset-derived results.

**Pseudocode:**
```
FOR ALL supplier_id IN current_supplier_dataset DO
  result_a := recommend_fixed(supplier_id)
  result_b := recommend_fixed(supplier_id)
  ASSERT result_a.ranking    = result_b.ranking
  ASSERT result_a.risk_score = result_b.risk_score
  IF result_a.replacement_required THEN
    ASSERT result_a.route.source_port IN route_dataset.source_port
    ASSERT result_a.route.destination_port IN route_dataset.destination_port
    ASSERT result_a.route.estimated_cost_usd > 0
    ASSERT result_a.route.estimated_delay_days >= 0
  END IF
END FOR
```

### Preservation Checking

**Goal**: Verify that error responses and no-replacement responses are unchanged.

**Pseudocode:**
```
FOR ALL supplier_id WHERE NOT isBugCondition(supplier_id) DO
  ASSERT recommend_original(supplier_id).status = recommend_fixed(supplier_id).status
  ASSERT recommend_original(supplier_id).error  = recommend_fixed(supplier_id).error
END FOR
```

**Test Cases:**
1. **Missing ID preservation**: POST with `{}` → still returns HTTP 400.
2. **Unknown ID preservation**: POST with `{"current_supplier_id": "CUR_999"}` → still returns
   HTTP 404.
3. **No-replacement preservation**: POST with a supplier whose country has low risk → response still
   contains `"Replacement Required": "No"` and no `"Top 4 Ranked Suppliers"` key.

### Unit Tests

- Test that `scenario_df` mean aggregation returns a Series with `supply_shortage`,
  `production_loss`, `cost_impact` keys.
- Test that `risk_df` country-group mean returns the correct deterministic risk score for `Russia`.
- Test that `RouteOptimizer.find_best_route("Dubai Port", "Rotterdam Port")` returns a non-None
  path.
- Test that the port-derivation logic returns a valid port name for countries present in
  `route_dataset.csv`.

### Property-Based Tests

- Generate random valid `current_supplier_id` values and assert that two calls always return
  identical top-4 rankings.
- Generate random valid `current_supplier_id` values where replacement is required and assert that
  the returned `source_port` appears in `route_dataset.csv`.
- Generate random valid `current_supplier_id` values and assert that `estimated_cost_usd` is a
  positive float derived from `cost_dataset.csv` (i.e., within the observed cost range).

### Integration Tests

- End-to-end: start the Flask app, POST to `/recommend` with `CUR_064` twice, assert identical
  JSON responses.
- Route validity: for every alternative in the top-4, assert `source_port → destination_port` is a
  traversable path in the `RouteOptimizer` graph.
- Cost range: assert `estimated_cost_usd` is between the min and max `total_cost` values in
  `cost_dataset.csv`.
