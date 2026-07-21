"""
Strategic Reserve Optimization Agent
Evaluation Script

Tests the advanced optimization agent against multiple resilience scenarios.
"""

import json
from pathlib import Path
from agent import StrategicReserveAgent

def get_base_input(horizon=7):
    return {
        "gap_data": {
            "daily_gap": [20.0] * horizon,
            "horizon": horizon,
            "confidence": 0.90
        },
        "demand_data": [
            {"id": "Refinery_A", "daily_demand": [100.0] * horizon, "priority": 2.0},
            {"id": "Refinery_B", "daily_demand": [80.0] * horizon, "priority": 1.5},
            {"id": "Refinery_C", "daily_demand": [50.0] * horizon, "priority": 1.0}
        ],
        "spr_data": {
            "current_inventory": 2000.0,
            "max_daily_drawdown": 100.0,
            "min_reserve_level": 500.0
        },
        "procurement_data": {
            "expected_incoming_shipments": [5.0] * horizon,
            "procurement_cost": [80.0] * horizon,
            "replenishment_lead_time": 2
        }
    }

def run_evaluations():
    agent = StrategicReserveAgent()
    results = {}
    
    # 1. Baseline Scenario
    print("Evaluating Baseline Scenario...")
    baseline = get_base_input()
    results["baseline"] = agent.optimize(baseline)
    
    # 2. Severe Supply Shock (High Gap, Low Shipments, High Prices)
    print("Evaluating Severe Supply Shock...")
    shock = get_base_input()
    shock["gap_data"]["daily_gap"] = [80.0, 90.0, 100.0, 110.0, 90.0, 80.0, 70.0]
    shock["gap_data"]["confidence"] = 0.95
    shock["procurement_data"]["expected_incoming_shipments"] = [0.0] * 7
    shock["procurement_data"]["procurement_cost"] = [110.0, 115.0, 120.0, 125.0, 120.0, 115.0, 110.0]
    results["severe_shock"] = agent.optimize(shock)
    
    # Save the output
    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("\nEvaluation complete. Results saved to outputs/evaluation_results.json")
    print("\nSample Output (Severe Shock):")
    print(json.dumps(results["severe_shock"], indent=2))

if __name__ == "__main__":
    run_evaluations()
