"""
Strategic Reserve Optimization Agent
Main Module

This Python module exposes the StrategicReserveAgent class, exactly 
matching the formal input and output schemas for the AI Resilience system.
"""

import json
import logging
from src.optimization.optimizer import StrategicReserveOptimizer

# Suppress internal solver logs when used as a pure module
logging.getLogger("src.optimization.optimizer").setLevel(logging.ERROR)

class StrategicReserveAgent:
    def __init__(self):
        self.optimizer = StrategicReserveOptimizer()
        
    def optimize(self, input_data: dict) -> dict:
        """
        Computes the optimal strategy based on the strict runtime inputs.
        
        Expected input_data keys:
        - gap_data: dict
        - demand_data: list of dicts
        - spr_data: dict
        - procurement_data: dict
        """
        # 1. Validate Schema
        required = ["gap_data", "demand_data", "spr_data", "procurement_data"]
        for k in required:
            if k not in input_data:
                raise ValueError(f"Missing required runtime input: {k}")
                
        # 2. Run Mathematical Optimization
        try:
            result = self.optimizer.solve(
                gap_data=input_data["gap_data"],
                demand_data=input_data["demand_data"],
                spr_data=input_data["spr_data"],
                procurement_data=input_data["procurement_data"]
            )
        except Exception as e:
            return {"error": str(e)}
            
        # 3. Generate Human-Readable Explanation
        total_release = sum(result["drawdown_schedule"])
        total_procured = sum(result["replenishment_plan"])
        
        explanation = (
            f"Based on a {input_data['gap_data']['horizon']}-day forecast with {input_data['gap_data']['confidence']*100:.0f}% confidence, "
        )
        if result["release_spr"]:
            explanation += (
                f"the optimizer recommends releasing a total of {total_release:.1f} units from the Strategic Petroleum Reserve. "
                f"This drawdown is explicitly allocated to high-priority refineries to minimize economic disruption. "
            )
        else:
            explanation += "the optimizer determined that SPR drawdown is not required. "
            
        if total_procured > 0:
            explanation += f"To ensure long-term stability and satisfy constraints, {total_procured:.1f} units of spot procurement are scheduled."
            
        result["explanation"] = explanation
        
        return result

# Only for simple testing when run directly
if __name__ == "__main__":
    agent = StrategicReserveAgent()
    
    mock_input = {
        "gap_data": {
            "daily_gap": [20.0, 30.0, 40.0, 50.0, 20.0],
            "horizon": 5,
            "confidence": 0.90
        },
        "demand_data": [
            {"id": "Refinery_A", "daily_demand": [100.0, 100.0, 100.0, 100.0, 100.0], "priority": 1.5},
            {"id": "Refinery_B", "daily_demand": [50.0, 50.0, 50.0, 50.0, 50.0], "priority": 1.0}
        ],
        "spr_data": {
            "current_inventory": 1500.0,
            "max_daily_drawdown": 80.0,
            "min_reserve_level": 500.0
        },
        "procurement_data": {
            "expected_incoming_shipments": [0.0, 0.0, 10.0, 10.0, 10.0],
            "procurement_cost": [85.0, 86.0, 90.0, 92.0, 85.0],
            "replenishment_lead_time": 2
        }
    }
    
    output = agent.optimize(mock_input)
    print(json.dumps(output, indent=2))
