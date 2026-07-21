from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional

# --- Module 1: Risk Intelligence ---
class RiskResponse(BaseModel):
    risk_class: str = Field(..., description="Predicted risk classification ('LOW', 'MEDIUM', 'HIGH')")
    risk_score: int = Field(..., description="Overall calculated risk score (0-100)")
    reasons: List[str] = Field(..., description="Root cause reasons explaining the risk rating")
    scenario: Optional[str] = Field(None, description="Name of the scenario applied for this assessment")

# --- Module 2: Scenario Simulation ---
class ScenarioInfo(BaseModel):
    scenario_id: int
    scenario_name: str
    scenario_type: str
    severity: str
    affected_route: str
    probability: float

class ScenarioListResponse(BaseModel):
    scenarios: List[ScenarioInfo]

class ScenarioEffectResponse(BaseModel):
    scenario_id: int
    scenario_name: str
    affected_route: str
    route_status: str
    extra_transit_time_days: int
    supply_reduction_pct: int
    transportation_cost_increase_pct: int
    estimated_shipping_delay_days: int
    brent_oil_price_increase_pct: int
    inventory_remaining_days: int
    demand_fulfillment_pct: int
    supplier_availability_pct: int
    overall_risk: str
    current_inventory: Optional[float] = None
    safety_stock: Optional[float] = None
    strategic_reserve: Optional[float] = None
    forecast_demand: Optional[float] = None
    current_demand: Optional[float] = None

# --- Module 3: Alternative Supplier Recommendation ---
class RecommendRequest(BaseModel):
    current_supplier_id: str
    risk_score: Optional[float] = None

class RouteRequest(BaseModel):
    selected_supplier: str

class DelayRequest(BaseModel):
    selected_supplier: str

class CostRequest(BaseModel):
    selected_supplier: str

class CompleteAnalysisRequest(BaseModel):
    current_supplier_id: str
    selected_supplier: str

class AlternativeSupplierInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    rank: int
    supplier_id: str
    supplier_name: str
    country: str
    ranking_score: float
    reason: str = Field(..., alias="Reason")

class RiskAssessment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    risk_score: float = Field(..., alias="Risk Score")
    risk_level: str = Field(..., alias="Risk Level")
    supply_shortage: str = Field(..., alias="Supply Shortage")
    production_loss: str = Field(..., alias="Production Loss")
    disruption_probability: str = Field(..., alias="Disruption Probability")
    conclusion: str = Field(..., alias="Conclusion")

class Decision(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    replacement_required: str = Field(..., alias="Replacement Required")

class RecommendResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    current_supplier: str = Field(..., alias="Current Supplier")
    current_supplier_country: str = Field(..., alias="Current Supplier Country")
    risk_assessment: RiskAssessment = Field(..., alias="Risk Assessment")
    decision: Decision = Field(..., alias="Decision")
    top_ranked_suppliers: Optional[List[AlternativeSupplierInfo]] = Field(None, alias="Top 4 Ranked Suppliers")

# --- Module 4: Strategic Petroleum Reserve Optimizer ---
class GapData(BaseModel):
    daily_gap: List[float]
    horizon: int
    confidence: float

class RefineryDemand(BaseModel):
    id: str
    daily_demand: List[float]
    priority: float

class SPRData(BaseModel):
    current_inventory: float
    max_daily_drawdown: float
    min_reserve_level: float

class ProcurementData(BaseModel):
    expected_incoming_shipments: List[float]
    procurement_cost: List[float]
    replenishment_lead_time: int

class OptimizeRequest(BaseModel):
    gap_data: GapData
    demand_data: List[RefineryDemand]
    spr_data: SPRData
    procurement_data: ProcurementData

class OptimizeResponse(BaseModel):
    release_spr: bool
    drawdown_schedule: List[float]
    refinery_allocation: Dict[str, List[float]]
    replenishment_plan: List[float]
    remaining_reserve: float
    estimated_total_cost: float
    optimization_score: float
    explanation: str

# --- Unified Orchestrator Models ---
class OrchestrateRequest(BaseModel):
    current_supplier_id: str = Field("CUR_001", description="ID of the supplier currently experiencing potential disruptions")
    selected_supplier: str = Field("UAE Energy Ltd 5", description="Target alternative supplier to test and optimize routing for")
    horizon_days: int = Field(7, description="Forecasting and optimization timeframe in days")
    risk_score_override: Optional[float] = Field(None, description="Optional risk score override (0-100) for testing low/medium/high risk propagation")
    scenario_id_override: Optional[int] = Field(None, description="Optional scenario ID override for testing specific scenario effects")

class OrchestrateResponse(BaseModel):
    risk_assessment: RiskResponse
    scenario_disruptions: List[ScenarioInfo]
    scenario_effects: ScenarioEffectResponse
    alternative_analysis: Dict[str, Any]
    spr_optimization: OptimizeResponse
