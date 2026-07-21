import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

from integration.adapters import (
    run_risk_assessment_pipeline,
    get_scenario_predictions,
    run_scenario_effects,
    get_supplier_adapter,
    run_strategic_optimization,
    get_refinery_demands,
    get_expected_incoming_shipments,
    get_base_supply_gap,
    get_scenario_details
)

logger = logging.getLogger(__name__)

def orchestrate_pipeline(
    current_supplier_id: str = "CUR_001",
    selected_supplier: str = "UAE Energy Ltd 5",
    horizon_days: int = 7,
    risk_score_override: float = None,
    scenario_id_override: int = None
) -> Dict[str, Any]:
    """
    Orchestrates the end-to-end supply chain risk and optimization pipeline:
    1. Runs global Risk Intelligence module to get daily macro risk level & score.
    2. Runs Scenario Simulation module and Alternative Supplier module concurrently.
       - Both modules execute independently (GIL-safe and thread-safe).
       - Both consume the dynamically predicted risk score from Phase 1.
    3. Aggregates outputs from all three modules simultaneously to generate the final SPR optimization.
    """
    logger.info("Starting concurrent integrated orchestrator pipeline...")

    # Step 1: Macro Risk Intelligence Assessment (Sync Trigger)
    logger.info("Executing Phase 1: Macro Risk Intelligence...")
    risk_res = run_risk_assessment_pipeline()
    
    risk_score = risk_score_override if risk_score_override is not None else risk_res["risk_score"]
    risk_class = (
        "HIGH" if risk_score > 70 else "MEDIUM" if risk_score > 40 else "LOW"
    ) if risk_score_override is not None else risk_res["risk_class"]
    
    # Overwrite risk_res with dynamic or overridden risk values
    risk_res["risk_score"] = int(risk_score)
    risk_res["risk_class"] = risk_class

    # Step 2: Trigger independent evaluators (Scenario & Supplier) concurrently
    logger.info("Launching independent evaluators concurrently via ThreadPoolExecutor...")
    
    def run_scenario_branch():
        logger.info("[Thread-Scenario] Predicting active scenarios...")
        scenarios = get_scenario_predictions(risk_score=risk_score)
        if not scenarios:
            raise RuntimeError("No disruption scenarios simulated.")
        
        # Pick the matched scenario if override is specified
        matched_scen = None
        if scenario_id_override is not None:
            for s in scenarios:
                if s["scenario_id"] == scenario_id_override:
                    matched_scen = s
                    break
            
            # If the overridden scenario ID is not in top 4, fetch details directly
            if matched_scen is None:
                try:
                    matched_scen = get_scenario_details(scenario_id_override, risk_score=risk_score)
                except Exception as e:
                    logger.warning(f"Could not load details for scenario ID {scenario_id_override}: {e}")
        
        top_scenario = matched_scen if matched_scen is not None else scenarios[0]
        scenario_id = top_scenario["scenario_id"]
        scenario_name = top_scenario["scenario_name"]
        scenario_prob = top_scenario["probability"]

        logger.info(f"[Thread-Scenario] Calculating downstream effects for scenario ID {scenario_id}...")
        effects = run_scenario_effects(scenario_id, scenario_name, scenario_prob, risk_score=risk_score)
        return scenarios, effects

    def run_supplier_branch():
        logger.info(f"[Thread-Supplier] Running recommendations using risk score {risk_score}...")
        supplier_adapter = get_supplier_adapter()
        
        # Supplier recommendation using dynamic risk score
        recommend = supplier_adapter.recommend_suppliers(current_supplier_id, risk_score=risk_score)
        
        # Shipping lane route optimization (Dijkstra)
        route = supplier_adapter.analyze_route(selected_supplier)
        
        # Shipping delay and cost forecasts
        delay = supplier_adapter.predict_delay(selected_supplier)
        cost = supplier_adapter.predict_cost(selected_supplier)

        alternative_analysis = {
            "current_supplier": recommend.get("Current Supplier"),
            "current_supplier_country": recommend.get("Current Supplier Country"),
            "risk_assessment": recommend.get("Risk Assessment"),
            "decision": recommend.get("Decision"),
            "top_ranked_suppliers": recommend.get("Top 4 Ranked Suppliers"),
            "selected_supplier": selected_supplier,
            "best_route": route.get("Best Route"),
            "distance_km": route.get("Distance"),
            "expected_delivery_days": route.get("Expected Delivery"),
            "predicted_delay": delay.get("Predicted Delay"),
            "actual_delivery": delay.get("Actual Delivery"),
            "transportation_cost": cost.get("Transportation Cost"),
            "insurance_cost": cost.get("Insurance Cost"),
            "fuel_cost": cost.get("Fuel Cost"),
            "logistics_cost": cost.get("Logistics Cost"),
            "predicted_total_cost": cost.get("Predicted Total Cost")
        }
        return alternative_analysis

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_scenario = executor.submit(run_scenario_branch)
        future_supplier = executor.submit(run_supplier_branch)

        # Wait for both independent thread runs to finish
        scenarios, effects_res = future_scenario.result()
        alternative_analysis = future_supplier.result()

    logger.info("Concurrent threads complete. Aggregating outputs for optimization...")

    # Step 3: Run Strategic Petroleum Reserve Optimizer (Sync Aggregator)
    
    # 3.1: Gap schedule calculation (Aggregates Risk score + Scenario supply reduction %)
    supply_reduction_pct = effects_res["supply_reduction_pct"]
    forecast_demand_val = effects_res.get("forecast_demand")
    current_demand_val = effects_res.get("current_demand")
    
    # Retrieve base daily gap dynamically from scenario demand forecast or fallback
    base_daily_gap = get_base_supply_gap(forecast_demand_val, current_demand_val)
    
    # Dynamic gap is scaled by BOTH scenario reduction severity AND risk intelligence confidence
    unmet_gap = base_daily_gap * (1.0 + (supply_reduction_pct / 100.0) * (risk_score / 100.0))
    daily_gap_schedule = [round(unmet_gap, 2)] * horizon_days

    # 3.2: Procurement pricing calculation (Aggregates Supplier price per barrel + Scenario price markup %)
    oil_price_inc_pct = effects_res["brent_oil_price_increase_pct"]
    
    # Retrieve alternative supplier details dynamically from the adapter public interface
    supplier_adapter = get_supplier_adapter()
    try:
        supplier_details = supplier_adapter.get_supplier_details(selected_supplier)
        base_procurement_cost = supplier_details["price_per_barrel"]
        supplier_lead_time = supplier_details["lead_time"]
    except Exception as e:
        logger.warning(f"Could not retrieve supplier details for {selected_supplier}: {e}")
        base_procurement_cost = 80.0
        supplier_lead_time = 2
        
    inflated_procurement_cost = base_procurement_cost * (1.0 + (oil_price_inc_pct / 100.0))
    procurement_cost_schedule = [round(inflated_procurement_cost, 2)] * horizon_days

    # 3.3: Lead time logic (Aggregates Supplier replacement status & lead time)
    replacement_required = alternative_analysis.get("decision", {}).get("Replacement Required") == "Yes"
    lead_time = 2  # Baseline default
    if replacement_required:
        lead_time = supplier_lead_time

    # 3.4: Confidence calibration (Aggregates Risk intelligence rating + Scenario occurrence probability)
    # The optimization model confidence combines the scenario probability and overall risk rating
    top_scenario = scenarios[0]
    scenario_prob = top_scenario["probability"]
    confidence_rating = round((scenario_prob / 100.0) * (1.0 - (risk_score / 200.0)), 2)
    # Ensure confidence stays in valid bounds
    confidence_rating = max(0.1, min(1.0, confidence_rating))

    # Retrieve demands and shipments dynamically from adapter datasets
    demand_data = get_refinery_demands(horizon_days)
    expected_incoming = get_expected_incoming_shipments(horizon_days)
    
    # Retrieve inventory data dynamically from the scenario effects response
    current_inventory = effects_res.get("current_inventory", 2000.0)
    min_reserve_level = effects_res.get("safety_stock", 500.0)
    
    # Derive maximum drawdown level dynamically or use safe limits
    strategic_reserve = effects_res.get("strategic_reserve", 3000.0)
    max_daily_drawdown = round(strategic_reserve * 0.05, 1) if strategic_reserve else 100.0
    if max_daily_drawdown <= 0:
        max_daily_drawdown = 100.0

    optimizer_input = {
        "gap_data": {
            "daily_gap": daily_gap_schedule,
            "horizon": horizon_days,
            "confidence": confidence_rating
        },
        "demand_data": demand_data,
        "spr_data": {
            "current_inventory": current_inventory,
            "max_daily_drawdown": max_daily_drawdown,
            "min_reserve_level": min_reserve_level
        },
        "procurement_data": {
            "expected_incoming_shipments": expected_incoming,
            "procurement_cost": procurement_cost_schedule,
            "replenishment_lead_time": lead_time
        }
    }

    opt_res = run_strategic_optimization(optimizer_input)

    # Unify results
    orchestrated_response = {
        "risk_assessment": {
            "risk_class": risk_class,
            "risk_score": risk_score,
            "reasons": risk_res["reasons"]
        },
        "scenario_disruptions": scenarios,
        "scenario_effects": effects_res,
        "alternative_analysis": alternative_analysis,
        "spr_optimization": opt_res
    }

    logger.info("Decoupled concurrent platform orchestrator pipeline execution complete.")
    return orchestrated_response
