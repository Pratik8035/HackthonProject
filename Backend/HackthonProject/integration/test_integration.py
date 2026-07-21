import sys
import unittest
from pathlib import Path

# Add root folder to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from integration.adapters import (
    run_risk_assessment_pipeline,
    get_scenario_predictions,
    run_scenario_effects,
    get_supplier_adapter,
    run_strategic_optimization,
    get_refinery_demands,
    get_expected_incoming_shipments,
    get_base_supply_gap
)
from integration.orchestrator import orchestrate_pipeline


class TestSupplyChainIntegration(unittest.TestCase):

    def test_phase_1_risk_assessment(self):
        """Verifies that the macro Risk Intelligence pipeline executes and returns valid risk classes/scores."""
        print("\nTesting Phase 1: Risk Assessment...")
        res = run_risk_assessment_pipeline()
        self.assertIn("risk_class", res)
        self.assertIn("risk_score", res)
        self.assertIn("reasons", res)
        self.assertIn(res["risk_class"], ["LOW", "MEDIUM", "HIGH"])
        self.assertTrue(0 <= res["risk_score"] <= 100)
        self.assertIsInstance(res["reasons"], list)
        print(f"-> Success! Predicted Class: {res['risk_class']} (Score: {res['risk_score']})")

    def test_phase_2_scenario_simulation(self):
        """Verifies scenario predictions output the top 4 scenarios and calculate effects correctly."""
        print("\nTesting Phase 2: Scenario Simulation...")
        scenarios = get_scenario_predictions()
        self.assertEqual(len(scenarios), 4)
        for s in scenarios:
            self.assertIn("scenario_id", s)
            self.assertIn("scenario_name", s)
            self.assertIn("scenario_type", s)
            self.assertIn("severity", s)
            self.assertIn("probability", s)
            self.assertTrue(0.0 <= s["probability"] <= 100.0)

        # Test downstream effects calculation for the first scenario
        top_scen = scenarios[0]
        print(f"-> Running effects calculation on Top Scenario: {top_scen['scenario_name']}...")
        effects = run_scenario_effects(top_scen["scenario_id"], top_scen["scenario_name"], top_scen["probability"])
        self.assertEqual(effects["scenario_id"], top_scen["scenario_id"])
        self.assertIn("supply_reduction_pct", effects)
        self.assertIn("transportation_cost_increase_pct", effects)
        self.assertIn("estimated_shipping_delay_days", effects)
        self.assertIn("inventory_remaining_days", effects)
        self.assertIn("demand_fulfillment_pct", effects)
        self.assertIn("overall_risk", effects)
        self.assertIn(effects["overall_risk"], ["LOW", "MEDIUM", "HIGH"])
        self.assertIn("current_inventory", effects)
        self.assertIn("safety_stock", effects)
        self.assertIn("strategic_reserve", effects)
        self.assertIn("forecast_demand", effects)
        self.assertIn("current_demand", effects)
        print(f"-> Success! Downstream Risk: {effects['overall_risk']} (Supply Red: {effects['supply_reduction_pct']}%)")

    def test_phase_3_alternative_suppliers(self):
        """Verifies alternative supplier recommendation, routing, delays, and pricing analysis."""
        print("\nTesting Phase 3: Alternative Supplier Analysis...")
        adapter = get_supplier_adapter()

        # recommend without override
        rec = adapter.recommend_suppliers("CUR_001")
        self.assertIn("Current Supplier", rec)
        self.assertIn("Decision", rec)
        self.assertIn("Replacement Required", rec["Decision"])
        
        # recommend with high risk_score override (forces replacement)
        rec_override = adapter.recommend_suppliers("CUR_001", risk_score=95.0)
        self.assertEqual(rec_override["Decision"]["Replacement Required"], "Yes")
        self.assertIn("Top 4 Ranked Suppliers", rec_override)
        self.assertEqual(len(rec_override["Top 4 Ranked Suppliers"]), 4)

        # Route Optimization, Delays, Costs
        target_supplier = "UAE Energy Ltd 5"
        route = adapter.analyze_route(target_supplier)
        self.assertIn("Best Route", route)
        self.assertGreater(route["Distance"], 0)
        self.assertGreater(route["Expected Delivery"], 0)

        delay = adapter.predict_delay(target_supplier)
        self.assertIn("Predicted Delay", delay)
        self.assertIn("Actual Delivery", delay)

        cost = adapter.predict_cost(target_supplier)
        self.assertIn("Predicted Total Cost", cost)
        
        # Test get_supplier_details
        details = adapter.get_supplier_details(target_supplier)
        self.assertEqual(details["supplier_name"], target_supplier)
        self.assertIn("price_per_barrel", details)
        self.assertIn("lead_time", details)
        self.assertIn("capacity", details)
        
        print(f"-> Success! Best route: {route['Best Route']} (Dist: {route['Distance']} km, Cost: {cost['Predicted Total Cost']})")

    def test_phase_4_spr_optimization(self):
        """Verifies that the MILP Google OR-Tools Strategic Reserve optimization solver runs correctly."""
        print("\nTesting Phase 4: Strategic Reserve Optimization Solver...")
        mock_input = {
            "gap_data": {
                "daily_gap": [25.0, 30.0, 35.0, 20.0, 20.0, 15.0, 15.0],
                "horizon": 7,
                "confidence": 0.85
            },
            "demand_data": [
                {"id": "Refinery_A", "daily_demand": [100.0]*7, "priority": 2.0},
                {"id": "Refinery_B", "daily_demand": [80.0]*7, "priority": 1.5},
                {"id": "Refinery_C", "daily_demand": [50.0]*7, "priority": 1.0}
            ],
            "spr_data": {
                "current_inventory": 1800.0,
                "max_daily_drawdown": 90.0,
                "min_reserve_level": 500.0
            },
            "procurement_data": {
                "expected_incoming_shipments": [5.0]*7,
                "procurement_cost": [85.0]*7,
                "replenishment_lead_time": 2
            }
        }
        res = run_strategic_optimization(mock_input)
        self.assertNotIn("error", res)
        self.assertIn("release_spr", res)
        self.assertIn("drawdown_schedule", res)
        self.assertIn("refinery_allocation", res)
        self.assertIn("replenishment_plan", res)
        self.assertIn("optimization_score", res)
        self.assertIn("explanation", res)
        print(f"-> Success! Optimization score: {res['optimization_score']} (Drawdown Total: {sum(res['drawdown_schedule'])} units)")

    def test_decoupled_data_helpers(self):
        """Verifies that the new helper functions correctly retrieve data from datasets instead of hardcoded values."""
        print("\nTesting Decoupled Data Helpers...")
        demands = get_refinery_demands(5)
        self.assertEqual(len(demands), 3)
        for d in demands:
            self.assertIn("id", d)
            self.assertEqual(len(d["daily_demand"]), 5)
            self.assertIn("priority", d)
            
        shipments = get_expected_incoming_shipments(5)
        self.assertEqual(len(shipments), 5)
        for s in shipments:
            self.assertGreater(s, 0)
            
        gap = get_base_supply_gap(100.0, 80.0)
        self.assertEqual(gap, 5.0) # (100 - 80) / 10 = 2.0, bounded between 5.0 and 50.0
        
        gap_default = get_base_supply_gap()
        self.assertEqual(gap_default, 20.0)
        print("-> Success! Decoupled data helpers returned correct values.")

    def test_end_to_end_orchestration(self):
        """Verifies the unified end-to-end cohesive pipeline runs successfully and couples all modules."""
        print("\nTesting End-to-End Orchestrated Pipeline...")
        res = orchestrate_pipeline(
            current_supplier_id="CUR_001",
            selected_supplier="UAE Energy Ltd 5",
            horizon_days=5
        )
        self.assertIn("risk_assessment", res)
        self.assertIn("scenario_disruptions", res)
        self.assertIn("scenario_effects", res)
        self.assertIn("alternative_analysis", res)
        self.assertIn("spr_optimization", res)
        
        # Verify coupling
        self.assertEqual(res["scenario_effects"]["scenario_id"], res["scenario_disruptions"][0]["scenario_id"])
        self.assertEqual(res["alternative_analysis"]["selected_supplier"], "UAE Energy Ltd 5")
        self.assertEqual(len(res["spr_optimization"]["drawdown_schedule"]), 5)
        print(f"-> Success! End-to-end orchestration complete. Total estimated cost: {res['spr_optimization']['estimated_total_cost']}")

    def test_dynamic_pipeline_propagation(self):
        """Verifies that changing input risk scores and scenarios significantly affects scenario outputs, alternative supplier decisions, and optimizer inputs/outputs."""
        print("\nTesting Dynamic Pipeline Propagation...")
        
        # Scenario A: Low Risk (score = 10.0, scenario = 2)
        res_a = orchestrate_pipeline(
            current_supplier_id="CUR_001",
            selected_supplier="UAE Energy Ltd 5",
            horizon_days=5,
            risk_score_override=10.0,
            scenario_id_override=2
        )
        
        # Scenario B: High Risk (score = 90.0, scenario = 1)
        res_b = orchestrate_pipeline(
            current_supplier_id="CUR_001",
            selected_supplier="UAE Energy Ltd 5",
            horizon_days=5,
            risk_score_override=90.0,
            scenario_id_override=1
        )
        
        # Verify Risk Propagation
        self.assertEqual(res_a["risk_assessment"]["risk_score"], 10)
        self.assertEqual(res_b["risk_assessment"]["risk_score"], 90)
        self.assertEqual(res_a["risk_assessment"]["risk_class"], "LOW")
        self.assertEqual(res_b["risk_assessment"]["risk_class"], "HIGH")
        
        # Verify Scenario Probabilities change due to dynamic risk score scaling
        prob_a = {s["scenario_id"]: s["probability"] for s in res_a["scenario_disruptions"]}
        prob_b = {s["scenario_id"]: s["probability"] for s in res_b["scenario_disruptions"]}
        self.assertNotEqual(prob_a, prob_b)
        
        # Verify Scenario Selection Overrides propagate
        self.assertEqual(res_a["scenario_effects"]["scenario_id"], 2)
        self.assertEqual(res_b["scenario_effects"]["scenario_id"], 1)
        
        # Verify Scenario effects change
        red_a = res_a["scenario_effects"]["supply_reduction_pct"]
        red_b = res_b["scenario_effects"]["supply_reduction_pct"]
        self.assertNotEqual(red_a, red_b)
        
        # Verify Alternative Supplier assessment changes (Low risk -> No replacement, High risk -> Replacement Required)
        decision_a = res_a["alternative_analysis"]["decision"]["Replacement Required"]
        decision_b = res_b["alternative_analysis"]["decision"]["Replacement Required"]
        self.assertEqual(decision_a, "No")
        self.assertEqual(decision_b, "Yes")
        
        # Verify Optimizer Inputs change
        cost_a = res_a["spr_optimization"]["estimated_total_cost"]
        cost_b = res_b["spr_optimization"]["estimated_total_cost"]
        self.assertNotEqual(cost_a, cost_b)
        print(f"-> Success! Dynamic propagation verified. Low Risk Cost: {cost_a} vs High Risk Cost: {cost_b}")

    def test_supplier_recommendation_endpoint(self):
        """Verifies successful supplier recommendation endpoint call and common failure scenarios (like invalid supplier ID)."""
        import requests
        print("\nTesting Supplier Recommendation Endpoint...")
        url = "http://127.0.0.1:8080/api/v1/supplier/recommend"
        
        # Test success scenario
        try:
            r = requests.post(url, json={"current_supplier_id": "CUR_001"})
            if r.status_code == 500:
                self.fail("Endpoint returned HTTP 500 Internal Server Error.")
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertIn("Current Supplier", data)
            self.assertIn("Decision", data)
            
            # Test failure scenario (invalid supplier ID)
            r_fail = requests.post(url, json={"current_supplier_id": "INVALID_ID"})
            self.assertEqual(r_fail.status_code, 404)
            print("-> Success! Supplier recommendation endpoint tested successfully.")
        except requests.exceptions.ConnectionError:
            print("-> Skipped: Local API server is not running on port 8080.")


if __name__ == "__main__":
    unittest.main()
