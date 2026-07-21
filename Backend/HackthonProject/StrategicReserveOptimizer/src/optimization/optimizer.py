"""
Strategic Reserve Optimization Agent
Core Optimization Engine (OR-Tools)

Implements advanced Mixed Integer Linear Programming to minimize
supply disruption and procurement costs, respecting strict priorities.
"""

from ortools.linear_solver import pywraplp
import numpy as np
import logging

logger = logging.getLogger(__name__)

class StrategicReserveOptimizer:
    def __init__(self):
        # Internal configuration (static knowledge)
        self.BASE_SHORTAGE_PENALTY = 10.0   # Base cost per kMT of unmet demand
        self.SPR_HOLDING_COST = 0.005       # Holding cost per kMT
        self.INLAND_PIPELINE_COST = 0.02    # Fixed inland transport cost factor
        self.SCIP_TIME_LIMIT_MS = 15000     # 15s solver limit for speed
        
    def solve(self, gap_data: dict, demand_data: list, spr_data: dict, procurement_data: dict) -> dict:
        """
        Solves the MILP routing and procurement problem.
        
        Args:
            gap_data: {"daily_gap": [...], "horizon": int, "confidence": float}
            demand_data: [{"id": str, "daily_demand": [...], "priority": float}, ...]
            spr_data: {"current_inventory": float, "max_daily_drawdown": float, "min_reserve_level": float}
            procurement_data: {"expected_incoming_shipments": [...], "procurement_cost": [...], "replenishment_lead_time": int}
        """
        horizon = gap_data["horizon"]
        T = range(horizon)
        refineries = [r["id"] for r in demand_data]
        
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            raise Exception("SCIP Solver not available.")
            
        solver.set_time_limit(self.SCIP_TIME_LIMIT_MS)
            
        # --- Decision Variables ---
        # Daily SPR Release
        spr_release = {t: solver.NumVar(0, spr_data["max_daily_drawdown"], f"spr_{t}") for t in T}
        
        # Allocation from SPR to Refinery r
        allocation = {}
        for r in refineries:
            for t in T:
                allocation[(r, t)] = solver.NumVar(0, solver.infinity(), f"alloc_{r}_{t}")
                
        # Shortage per refinery
        shortage = {}
        for r in refineries:
            for t in T:
                shortage[(r, t)] = solver.NumVar(0, solver.infinity(), f"short_{r}_{t}")
                
        # SPR Inventory
        inventory = {t: solver.NumVar(spr_data["min_reserve_level"], solver.infinity(), f"inv_{t}") for t in T}
        
        # New Procurement (overseas spot purchases triggered by the agent)
        procure = {t: solver.NumVar(0, solver.infinity(), f"procure_{t}") for t in T}
        
        # Binary trigger for SPR usage penalty
        use_spr = {t: solver.IntVar(0, 1, f"use_spr_{t}") for t in T}
        
        # --- Constraints ---
        
        # 1. SPR Inventory Balance
        for t in T:
            prev_inv = spr_data["current_inventory"] if t == 0 else inventory[t-1]
            
            # Inventory changes by what we release, PLUS what we replenish.
            # Replenishment arrives after 'lead_time'
            lead_time = procurement_data["replenishment_lead_time"]
            replenished = procure[t - lead_time] if (t - lead_time) >= 0 else 0
            
            solver.Add(inventory[t] == prev_inv - spr_release[t] + replenished)
            
        # 2. SPR Release to Allocation mapping
        for t in T:
            # The total SPR released must equal the sum of allocations to refineries
            solver.Add(sum(allocation[(r, t)] for r in refineries) == spr_release[t])
            
            # Big-M constraint to flag SPR usage
            M = spr_data["max_daily_drawdown"] * 10
            solver.Add(spr_release[t] <= M * use_spr[t])
            
        # 3. National Supply-Demand Balance per Refinery
        for t in T:
            daily_gap = gap_data["daily_gap"][t]
            expected_incoming = procurement_data["expected_incoming_shipments"][t]
            
            for req in demand_data:
                r = req["id"]
                daily_dem = req["daily_demand"][t]
                
                # To isolate refinery gap, we assume the 'national daily gap' is proportionally distributed 
                # unless offset by expected incoming shipments.
                # A simplified constraint: Refinery gets its baseline supply + SPR allocation + Shortage == Demand
                # Baseline supply = Demand - (Proportional Gap) + (Proportional Incoming)
                
                total_dem = sum(d["daily_demand"][t] for d in demand_data)
                prop = daily_dem / total_dem if total_dem > 0 else 0
                
                # The refinery's specific unmet need before SPR
                refinery_baseline_shortfall = (daily_gap * prop) - (expected_incoming * prop)
                if refinery_baseline_shortfall < 0: 
                    refinery_baseline_shortfall = 0
                    
                solver.Add(allocation[(r, t)] + shortage[(r, t)] >= refinery_baseline_shortfall)
                
        # --- Objective Function ---
        objective = solver.Objective()
        
        # 1. Penalize Shortages based on Priority
        for t in T:
            for req in demand_data:
                r = req["id"]
                weight = req["priority"]
                # Higher priority = higher penalty for shortage
                penalty = self.BASE_SHORTAGE_PENALTY * weight
                objective.SetCoefficient(shortage[(r, t)], penalty)
                
        # 2. Procurement Costs
        for t in T:
            cost = procurement_data["procurement_cost"][t]
            objective.SetCoefficient(procure[t], cost)
            
        # 3. SPR Usage & Holding Costs
        for t in T:
            objective.SetCoefficient(use_spr[t], 1.0) # Small penalty for tapping SPR
            objective.SetCoefficient(inventory[t], self.SPR_HOLDING_COST)
            
        # 4. Inland Pipeline Costs
        for t in T:
            for r in refineries:
                objective.SetCoefficient(allocation[(r, t)], self.INLAND_PIPELINE_COST)
                
        objective.SetMinimization()
        
        # --- Solve ---
        logger.info("Starting advanced MILP optimization (SCIP)...")
        status = solver.Solve()
        
        if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            total_cost = objective.Value()
            
            schedule = []
            allocations = {r: [] for r in refineries}
            replenishment = []
            
            is_spr_used = False
            
            for t in T:
                released = round(spr_release[t].solution_value(), 2)
                if released > 0: is_spr_used = True
                    
                schedule.append(released)
                replenishment.append(round(procure[t].solution_value(), 2))
                
                for r in refineries:
                    allocations[r].append(round(allocation[(r, t)].solution_value(), 2))
                    
            final_inventory = round(inventory[horizon-1].solution_value(), 2)
            
            # Normalizing score (0 to 100) based on confidence and gap
            # Highly confident plans with optimal status get high scores.
            score = 95.0 if status == pywraplp.Solver.OPTIMAL else 75.0
            score *= gap_data["confidence"]
            
            result = {
                "release_spr": is_spr_used,
                "drawdown_schedule": schedule,
                "refinery_allocation": allocations,
                "replenishment_plan": replenishment,
                "remaining_reserve": final_inventory,
                "estimated_total_cost": round(total_cost, 2),
                "optimization_score": round(score, 1)
            }
            return result
        else:
            raise RuntimeError("Optimizer failed to find a feasible solution under the given constraints.")
