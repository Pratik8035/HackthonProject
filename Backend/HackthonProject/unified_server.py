import json
import logging
from fastapi import FastAPI, Header, Body, HTTPException, Query
from typing import Dict, Any, List

from integration.models import (
    RiskResponse,
    ScenarioListResponse,
    ScenarioEffectResponse,
    RecommendResponse,
    OptimizeRequest,
    OptimizeResponse,
    OrchestrateRequest,
    OrchestrateResponse,
    RecommendRequest,
    RouteRequest,
    DelayRequest,
    CostRequest,
    CompleteAnalysisRequest
)
from integration.adapters import (
    run_risk_assessment_pipeline,
    get_scenario_predictions,
    run_scenario_effects,
    get_supplier_adapter,
    run_strategic_optimization
)
from integration.orchestrator import orchestrate_pipeline

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("unified_server")

app = FastAPI(
    title="Supply Chain Risk & Strategic Reserve Resilience Platform API",
    description="Unified API Gateway integrating Risk Intelligence, Scenario Simulation, Supplier Recommendations, and SPR Optimization.",
    version="1.0.0"
)

# ---------------------------------------------------------------------------
# Home & Health Checks
# ---------------------------------------------------------------------------
@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Unified Supply Chain Resilience API Gateway is running.",
        "docs_url": "/docs"
    }


# ---------------------------------------------------------------------------
# Module 1: Risk Intelligence
# ---------------------------------------------------------------------------
@app.get("/api/v1/risk/run", response_model=RiskResponse, tags=["Module 1: Risk Intelligence"])
def run_risk_assessment():
    """Triggers the daily Risk Intelligence assessment pipeline."""
    try:
        results = run_risk_assessment_pipeline()
        return results
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Module 2: Scenario Simulation & Downstream Effects
# ---------------------------------------------------------------------------
@app.get("/api/v1/scenario/list", response_model=ScenarioListResponse, tags=["Module 2: Scenario Simulation"])
def list_scenarios(risk_score: float = Query(None, description="Live risk score (0-100) to weight scenario probabilities")):
    """Predicts active scenarios and lists the top 4 candidates with probabilities."""
    try:
        scenarios = get_scenario_predictions(risk_score=risk_score)
        return {"scenarios": scenarios}
    except Exception as e:
        logger.error(f"Listing scenarios failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/scenario/effects", response_model=ScenarioEffectResponse, tags=["Module 2: Scenario Simulation"])
def run_effects(
    scenario_id: int = Query(..., description="ID of the scenario to simulate"),
    scenario_name: str = Query(..., description="Name of the scenario to simulate"),
    probability: float = Query(..., description="Calculated probability of the scenario")
):
    """Calculates downstream effects (costs, delays, price spikes) of a chosen scenario."""
    try:
        effects = run_scenario_effects(scenario_id, scenario_name, probability)
        return effects
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Downstream effects prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Module 3: Alternative Supplier Recommendation
# ---------------------------------------------------------------------------
@app.get("/api/v1/supplier/current", tags=["Module 3: Alternative Suppliers"])
def list_current_suppliers():
    """Retrieves all current suppliers in the database."""
    try:
        adapter = get_supplier_adapter()
        return adapter.current_df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Failed to fetch current suppliers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/supplier/recommend", response_model=RecommendResponse, tags=["Module 3: Alternative Suppliers"])
def recommend_supplier(req: RecommendRequest):
    """Determines current supplier risk and recommends ranked alternatives if high risk."""
    try:
        adapter = get_supplier_adapter()
        recommendation = adapter.recommend_suppliers(req.current_supplier_id, risk_score=req.risk_score)
        return recommendation
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except Exception as e:
        logger.exception("Supplier recommendation failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/supplier/route", tags=["Module 3: Alternative Suppliers"])
def analyze_supplier_route(req: RouteRequest):
    """Computes the optimized transportation route distance and transit days."""
    try:
        adapter = get_supplier_adapter()
        route_info = adapter.analyze_route(req.selected_supplier)
        return route_info
    except Exception as e:
        logger.error(f"Route optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/supplier/delay", tags=["Module 3: Alternative Suppliers"])
def predict_supplier_delay(req: DelayRequest):
    """Predicts shipping delays using Random Forest Regressor models."""
    try:
        adapter = get_supplier_adapter()
        delay_info = adapter.predict_delay(req.selected_supplier)
        return delay_info
    except Exception as e:
        logger.error(f"Delay prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/supplier/cost", tags=["Module 3: Alternative Suppliers"])
def predict_supplier_cost(req: CostRequest):
    """Predicts transportation, fuel, and insurance costs."""
    try:
        adapter = get_supplier_adapter()
        cost_info = adapter.predict_cost(req.selected_supplier)
        return cost_info
    except Exception as e:
        logger.error(f"Cost prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/supplier/complete-analysis", tags=["Module 3: Alternative Suppliers"])
def run_complete_supplier_analysis(req: CompleteAnalysisRequest):
    """Orchestrates supplier recommendations and predicted routes/delays/costs."""
    try:
        adapter = get_supplier_adapter()
        
        # Recommendation
        rec_res = adapter.recommend_suppliers(req.current_supplier_id)
        decision = rec_res.get("Decision", {})
        
        if decision.get("Replacement Required") == "No":
            return {
                "Current Supplier": rec_res.get("Current Supplier"),
                "Current Supplier Country": rec_res.get("Current Supplier Country"),
                "Risk Assessment": rec_res.get("Risk Assessment"),
                "Decision": decision,
                "Final Recommendation": "Current supplier is safe. No alternative supplier recommendation. Processing stopped."
            }

        # Sub-analysis runs
        route_res = adapter.analyze_route(req.selected_supplier)
        delay_res = adapter.predict_delay(req.selected_supplier)
        cost_res = adapter.predict_cost(req.selected_supplier)

        return {
            "Current Supplier": rec_res.get("Current Supplier"),
            "Current Supplier Country": rec_res.get("Current Supplier Country"),
            "Risk Assessment": rec_res.get("Risk Assessment"),
            "Decision": decision,
            "Top Ranked Suppliers": rec_res.get("Top 4 Ranked Suppliers"),
            "Selected Supplier": req.selected_supplier,
            "Best Route": route_res.get("Best Route"),
            "Shortest Distance": f"{route_res.get('Distance')} km",
            "Expected Delivery": f"{route_res.get('Expected Delivery')} Days",
            "Predicted Delay": delay_res.get("Predicted Delay"),
            "Actual Delivery": delay_res.get("Actual Delivery"),
            "Transportation Cost": cost_res.get("Transportation Cost"),
            "Insurance Cost": cost_res.get("Insurance Cost"),
            "Fuel Cost": cost_res.get("Fuel Cost"),
            "Logistics Cost": cost_res.get("Logistics Cost"),
            "Predicted Total Cost": cost_res.get("Predicted Total Cost"),
            "Final Recommendation": f"Proceed with {req.selected_supplier} via {route_res.get('Best Route')}."
        }
    except Exception as e:
        logger.error(f"Complete supplier analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Module 4: Strategic Petroleum Reserve Optimizer
# ---------------------------------------------------------------------------
@app.post("/api/v1/optimize", response_model=OptimizeResponse, tags=["Module 4: SPR Optimization"])
def optimize_reserves(
    agent_input_header: str = Header(None, alias="X-Agent-Input"),
    agent_input_body: OptimizeRequest = Body(None)
):
    """
    Optimizes daily SPR release schedules, replenishment plans, and refinery routing.
    Accepts input via request body or 'X-Agent-Input' header matching the formal schema.
    """
    input_data = None
    if agent_input_header:
        try:
            input_data = json.loads(agent_input_header)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in X-Agent-Input header")
    elif agent_input_body:
        # Convert Pydantic model to Dict
        input_data = agent_input_body.model_dump()

    if not input_data:
        raise HTTPException(status_code=400, detail="Missing input data. Provide via Body or X-Agent-Input header.")

    try:
        recommendation = run_strategic_optimization(input_data)
        if "error" in recommendation:
            raise HTTPException(status_code=400, detail=recommendation["error"])
        return recommendation
    except Exception as e:
        logger.error(f"SPR Optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Unified Cohesive Orchestration Endpoint
# ---------------------------------------------------------------------------
@app.post("/api/v1/orchestrate", response_model=OrchestrateResponse, tags=["Cohesive End-to-End Orchestrator"])
def orchestrate_pipeline_endpoint(req: OrchestrateRequest):
    """
    Executes the cohesive end-to-end integration workflow.
    Feeds predicted supply chain risks and cost inflation directly into the SPR optimization agent.
    """
    try:
        result = orchestrate_pipeline(
            current_supplier_id=req.current_supplier_id,
            selected_supplier=req.selected_supplier,
            horizon_days=req.horizon_days,
            risk_score_override=req.risk_score_override,
            scenario_id_override=req.scenario_id_override
        )
        return result
    except Exception as e:
        logger.exception("Unified orchestration failed")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # Start the unified server on port 8080
    uvicorn.run(app, host="127.0.0.1", port=8080)
