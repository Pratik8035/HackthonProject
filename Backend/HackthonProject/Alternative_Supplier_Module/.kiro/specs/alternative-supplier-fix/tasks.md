# Implementation Plan

## Overview

Two bugs in `routes/supplier_api.py` are addressed using the exploratory bugfix workflow:

- **Bug 1 — Non-Deterministic Output**: `scenario_df.sample(1)`, `risk_df.sample(1)`, and any other
  random calls produce different rankings, risk scores, routes, costs, and delays on every API call
  even when datasets are unchanged.
- **Bug 2 — Incorrect Route / Cost / Delay**: Route, cost, and delay values were not fetched from
  `route_dataset.csv`, `cost_dataset.csv`, or `delay_dataset.csv` but were fabricated randomly.

Only `routes/supplier_api.py` is modified. No other files are touched.

---

## Tasks

- [ ] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Non-Deterministic Recommendation & Missing Route Data
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms both bugs exist
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: The test encodes expected behavior; it will validate the fix once it passes after implementation
  - **GOAL**: Surface counterexamples that prove randomness and absent route data exist in the unfixed code
  - **Scoped PBT Approach**: Scope to a small fixed set of `current_supplier_id` values (e.g., `CUR_064`, `CUR_001`) so the property is deterministically reproducible
  - **Bug 1 sub-test** — call `/recommend` (or invoke `recommend_suppliers` directly) twice with
    the same `current_supplier_id`; assert that at least one of the following differs between the
    two calls:
    - `result["Top 4 Ranked Suppliers"]` ranking order
    - `result["Risk Assessment"]["Risk Score"]`
  - **Bug 2 sub-test** — call `/recommend` once and assert that every entry in
    `result["Top 4 Ranked Suppliers"]` either lacks the `Route` key or has `Route.source_port`
    not present in `route_dataset.csv`
  - Run the test against the **UNFIXED** code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the bugs exist)
  - Document the counterexamples found (e.g., `CUR_064` produces different `Risk Score` values;
    `Route` key is absent entirely)
  - Mark task complete when the test is written, executed, and the failure is documented
  - _Bug_Condition: isBugCondition(call_a_result, call_b_result) where call_a_result.ranking !=
    call_b_result.ranking OR call_a_result.risk_score != call_b_result.risk_score OR Route key
    absent from response_
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

- [ ] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Error Responses and No-Replacement Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe on **UNFIXED** code:
    - `POST /recommend` with `{}` → HTTP 400
    - `POST /recommend` with `{"current_supplier_id": "CUR_999"}` → HTTP 404
    - `GET /current-suppliers` → full list from `current_supplier_dataset.csv` (count matches)
    - `POST /recommend` with a low-risk supplier → response contains `"Replacement Required": "No"` and no `"Top 4 Ranked Suppliers"` key
  - Write property-based tests that assert the above behaviors hold for all inputs where the bug
    condition does NOT apply (i.e., inputs that do not involve random sampling or route lookup):
    - For all missing-`current_supplier_id` requests → always HTTP 400
    - For all unknown `current_supplier_id` values → always HTTP 404
    - For all low-risk suppliers (risk_score ≤ 70, prob ≤ 60%, shortage ≤ 30%, loss ≤ 25%) →
      response always has `"Replacement Required": "No"` and no alternatives list
  - Run tests on **UNFIXED** code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior to preserve)
  - Mark task complete when tests are written, executed, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ] 3. Fix `routes/supplier_api.py` — remove randomness and add dataset-driven route lookup

  - [ ] 3.1 Remove `import random` and eliminate all `random.*` / `.sample()` calls
    - Delete the `import random` statement at the top of the file
    - Replace `scenario_df.sample(1).iloc[0]` with the global mean of numeric columns:
      `scenario_df[['supply_shortage', 'production_loss', 'cost_impact']].mean()`
      stored as the module-level constant `_scen_agg`
    - Replace `risk_df.sample(1)` fallback with a mean-aggregation fallback:
      `risk_df[['risk_score']].mean()` with hardcoded `risk_level = 'Medium Risk'` and
      `disruption_probability = 'Medium'`
    - Replace any `risk_df.iloc[0]` per-country selection with a `.groupby('supplier_country')`
      aggregation that takes `mean()` of `risk_score` and `mode()[0]` of `risk_level` /
      `disruption_probability`, stored as module-level dict `_risk_agg`
    - Pre-compute `_scen_agg` and `_risk_agg` once at module load so every request reads from
      these deterministic objects
    - _Bug_Condition: any call to `random.*`, `df.sample()`, or non-deterministic row selection_
    - _Expected_Behavior: `_scen_agg` and `_risk_agg` are identical on every invocation for
      unchanged datasets; `recommend_suppliers` uses only these pre-computed values_
    - _Preservation: error responses, risk threshold logic, ranking model, API structure unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 3.2 Add `COUNTRY_PORT_MAP` and load `route_dataset.csv`, `cost_dataset.csv`, `delay_dataset.csv`
    - Add `COUNTRY_PORT_MAP` dict mapping supplier country strings to their nearest major port
      (deterministic, hardcoded geographic heuristic)
    - Load `route_df`, `cost_df`, `delay_df` with `pd.read_csv(...)` at module level alongside
      the other dataset loads
    - _Requirements: 2.6_

  - [ ] 3.3 Implement `_get_route_info(alt_country, curr_country)` helper
    - Map both countries to ports via `COUNTRY_PORT_MAP`; return `Unknown` placeholders if either
      country is missing from the map (graceful fallback — requirement 3.7)
    - Filter `route_df` for rows where `source_port == alt_port AND destination_port == curr_port`;
      take the row with minimum `distance_km` (deterministic tiebreaker)
    - If no direct row exists, call `RouteOptimizer.find_best_route(alt_port, curr_port)`;
      if that also returns no path, fall back to global means of `route_df`
    - Derive `estimated_cost_usd` as mean `total_cost` from `cost_df` where
      `abs(cost_df['distance_km'] - distance_km) <= 2000`, else global mean of `cost_df`
    - Derive `estimated_delay_days` as mean `delay_days` from `delay_df` where
      `abs(delay_df['distance_km'] - distance_km) <= 2000`, else global mean of `delay_df`
    - Return a dict with keys `source_port`, `destination_port`, `distance_km`,
      `expected_transit_days`, `estimated_cost_usd`, `estimated_delay_days`
    - _Bug_Condition: route/cost/delay not present in response or not derived from CSV datasets_
    - _Expected_Behavior: all route fields populated from dataset lookups; values reproducible_
    - _Preservation: function is purely additive; existing response fields unaffected_
    - _Requirements: 2.6, 2.7, 2.8, 3.7_

  - [ ] 3.4 Call `_get_route_info` for each top-4 alternative and include `Route` key in response
    - In the `recommend_suppliers` loop over `top_4`, call
      `route_info = _get_route_info(row.country, supp_info['country'])`
    - Add `"Route": route_info` to each alternative dict
    - _Requirements: 2.6, 2.7, 2.8_

  - [ ] 3.5 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Deterministic Output and Dataset-Derived Route
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior for both Bug 1 and Bug 2
    - When this test passes it confirms:
      - Two identical calls return the same ranking and risk score (Bug 1 fixed)
      - Every alternative's `Route.source_port` appears in `route_dataset.csv` (Bug 2 fixed)
    - Run the bug condition exploration test from step 1 against the **FIXED** code
    - **EXPECTED OUTCOME**: Test PASSES (confirms both bugs are fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [ ] 3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Error Responses and No-Replacement Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2 against the **FIXED** code
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm HTTP 400, HTTP 404, no-replacement responses, and `/current-suppliers` output are
      all identical to unfixed behavior
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ] 4. Checkpoint — Ensure all tests pass
  - Re-run the full test suite (exploration test + preservation tests)
  - Confirm zero failures; ask the user if any ambiguities arise
  - Verify `routes/supplier_api.py` is the only file that was modified
  - Confirm no new folders or files were created

---

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1", "2"]
    },
    {
      "wave": 2,
      "tasks": ["3.1", "3.2"]
    },
    {
      "wave": 3,
      "tasks": ["3.3"]
    },
    {
      "wave": 4,
      "tasks": ["3.4"]
    },
    {
      "wave": 5,
      "tasks": ["3.5", "3.6"]
    },
    {
      "wave": 6,
      "tasks": ["4"]
    }
  ]
}
```

---

## Notes

- Only `routes/supplier_api.py` is in scope. Do not modify `utils/preprocessing.py`,
  `utils/route_optimizer.py`, `app.py`, training scripts, or model files.
- Do not create new folders or files.
- Tasks 1 and 2 MUST be completed (and test results documented) before beginning Task 3.
- The `RouteOptimizer` in `utils/route_optimizer.py` already provides deterministic Dijkstra
  routing — no structural changes to it are needed; only the call from `supplier_api.py` matters.
- The `COUNTRY_PORT_MAP` is a hardcoded geographic heuristic; it covers all countries present in
  `alternative_supplier_dataset.csv`. If a country is not in the map, `_get_route_info` returns
  `Unknown` placeholders gracefully (satisfies requirement 3.7).
