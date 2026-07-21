import os
import sys
import pickle
import pandas as pd
import numpy as np
import joblib
import networkx as nx
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Any, Tuple

from integration.config import RISK_DIR, ALTERNATIVE_DIR, SCENARIO_DIR, STRATEGIC_DIR

# ---------------------------------------------------------------------------
# 1. Namespace Isolation Context Manager (for upfront startup imports)
# ---------------------------------------------------------------------------
@contextmanager
def module_namespace_context(target_dir: Path):
    """
    Temporarily adds the target directory to sys.path and removes conflicting 
    module names from sys.modules cache to ensure correct imports. Restores
    everything upon exit.
    """
    target_str = str(target_dir)
    original_path = sys.path.copy()
    sys.path.insert(0, target_str)
    
    # Modules that might conflict between Risk Intelligence and Scenario Modules
    conflicts = ['preprocessing', 'feature_engineering', 'predict_risk', 'shap_explainer', 'run_module', 'scenario_generator']
    saved_modules = {name: sys.modules.get(name) for name in conflicts if name in sys.modules}
    
    for name in conflicts:
        if name in sys.modules:
            del sys.modules[name]
            
    try:
        yield
    finally:
        sys.path = original_path
        for name in conflicts:
            if name in saved_modules:
                sys.modules[name] = saved_modules[name]
            elif name in sys.modules:
                del sys.modules[name]


# ---------------------------------------------------------------------------
# 2. Upfront Synchronous Imports at Startup (guarantees thread safety at runtime)
# ---------------------------------------------------------------------------
# Load Risk Intelligence module scripts
with module_namespace_context(RISK_DIR / "scripts"):
    import preprocessing as risk_prep
    import feature_engineering as risk_feat
    import predict_risk as risk_pred
    import shap_explainer as risk_shap
    import risk_reason_engine as risk_reasons
    import scenario_generator as risk_scenario

# Load Scenario Module scripts
with module_namespace_context(SCENARIO_DIR / "scripts"):
    import preprocessing as scen_prep
    import feature_engineering as scen_feat

# Load Strategic Petroleum Reserve Optimizer agent
original_path = sys.path.copy()
sys.path.insert(0, str(STRATEGIC_DIR))
try:
    from agent import StrategicReserveAgent
finally:
    sys.path = original_path


# ---------------------------------------------------------------------------
# 3. Risk Intelligence Module Adapter (GIL-safe, no runtime imports)
# ---------------------------------------------------------------------------
def run_risk_assessment_pipeline() -> Dict[str, Any]:
    """Runs the root Risk Intelligence prediction pipeline and returns risk results."""
    # Step 0: Apply a scenario to the source CSVs (rotates LOW / MEDIUM / HIGH each call)
    scenario_name = risk_scenario.generate_scenario()

    # Step 1: Preprocess and Merge
    preprocessed_df = risk_prep.preprocess_all()

    # Step 2: Feature Engineer (saves engineered_risk_dataset.csv)
    risk_feat.run_feature_engineering(preprocessed_df)

    # Step 3: Predict Risk
    risk_class, risk_score = risk_pred.predict_risk()

    # Step 4: SHAP explainer
    shap_df = risk_shap.explain_prediction()

    # Step 5: Risk Reasons
    reasons_df = risk_reasons.generate_reasons(shap_df, risk_class)
    reasons_list = reasons_df.head(4)["Reason"].tolist()

    return {
        "risk_class": risk_class,
        "risk_score": int(risk_score),
        "reasons": reasons_list,
        "scenario": scenario_name,
    }


# ---------------------------------------------------------------------------
# 4. Scenario Module Adapter (GIL-safe, no runtime imports)
# ---------------------------------------------------------------------------
def get_scenario_predictions(risk_score: float = None) -> List[Dict[str, Any]]:
    """Loads Scenario Module models and predicts disruption probabilities for scenarios."""
    models_dir = SCENARIO_DIR / "models"
    data_dir = SCENARIO_DIR / "datasets"

    # Load scenario models
    with open(models_dir / "scenario_model.pkl", "rb") as f:
        clf = pickle.load(f)
    with open(models_dir / "scenario_scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open(models_dir / "scenario_encoder.pkl", "rb") as f:
        encoders = pickle.load(f)

    # Load & Engineer
    datasets = scen_prep.load_all_datasets(str(data_dir))
    if risk_score is not None:
        factor = float(risk_score) / 50.0
        for col in ['Conflict Score', 'Sanction Score', 'Port Congestion Score']:
            if col in datasets['live_risk_output'].columns:
                datasets['live_risk_output'][col] = (datasets['live_risk_output'][col] * factor).clip(0.0, 100.0)
        if 'Current Risk Score' in datasets['live_risk_output'].columns:
            datasets['live_risk_output']['Current Risk Score'] = float(risk_score)

    df = scen_feat.engineer_features(datasets)

    categorical_cols = ['Scenario Type', 'Severity', 'Affected Region', 'Affected Commodity', 'Affected Route']
    engineered_cols = [
        'Conflict Score Feature', 'Shipping Risk', 'Oil Price Change', 'Port Congestion Index',
        'Supplier Reliability', 'Inventory Buffer', 'Demand Pressure', 'Transportation Cost Index',
        'Route Availability', 'Sanction Exposure'
    ]

    # Preprocess
    df_processed, _ = scen_prep.preprocess_categorical(
        df.copy(), categorical_cols, str(models_dir), 'scenario_encoder.pkl', mode='predict', encoders=encoders
    )
    df_processed, _ = scen_feat.scale_features(
        df_processed, engineered_cols, str(models_dir), 'scenario_scaler.pkl', mode='predict', scaler=scaler
    )

    X = df_processed[engineered_cols + categorical_cols]
    probs = clf.predict_proba(X)[:, 1]

    scenarios_df = df[['Scenario ID', 'Scenario Name', 'Scenario Type', 'Severity', 'Affected Route']].copy()
    scenarios_df['probability'] = (probs * 100).round(1)

    # Strip numeric suffix for base name
    def get_base_name(name):
        parts = name.split(' ')
        if parts and parts[-1].isdigit():
            return ' '.join(parts[:-1])
        return name

    scenarios_df['Base Name'] = scenarios_df['Scenario Name'].apply(get_base_name)
    scenarios_sorted = scenarios_df.sort_values(by='probability', ascending=False)
    scenarios_deduped = scenarios_sorted.drop_duplicates(subset='Base Name', keep='first')

    top_4 = scenarios_deduped.head(4).reset_index(drop=True)
    results = []
    for _, row in top_4.iterrows():
        results.append({
            "scenario_id": int(row["Scenario ID"]),
            "scenario_name": str(row["Base Name"]),
            "scenario_type": str(row["Scenario Type"]),
            "severity": str(row["Severity"]),
            "affected_route": str(row["Affected Route"]),
            "probability": float(row["probability"])
        })
    return results


def get_scenario_details(scenario_id: int, risk_score: float = None) -> Dict[str, Any]:
    """Retrieves scenario details directly from datasets by ID, with dynamic risk score scaling."""
    models_dir = SCENARIO_DIR / "models"
    data_dir = SCENARIO_DIR / "datasets"

    # Load scenario models
    with open(models_dir / "scenario_model.pkl", "rb") as f:
        clf = pickle.load(f)
    with open(models_dir / "scenario_scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open(models_dir / "scenario_encoder.pkl", "rb") as f:
        encoders = pickle.load(f)

    # Load & Engineer
    datasets = scen_prep.load_all_datasets(str(data_dir))
    if risk_score is not None:
        factor = float(risk_score) / 50.0
        for col in ['Conflict Score', 'Sanction Score', 'Port Congestion Score']:
            if col in datasets['live_risk_output'].columns:
                datasets['live_risk_output'][col] = (datasets['live_risk_output'][col] * factor).clip(0.0, 100.0)
        if 'Current Risk Score' in datasets['live_risk_output'].columns:
            datasets['live_risk_output']['Current Risk Score'] = float(risk_score)

    df = scen_feat.engineer_features(datasets)
    scenario_row = df[df['Scenario ID'] == scenario_id]
    if scenario_row.empty:
        raise ValueError(f"Scenario ID {scenario_id} not found in master list.")

    row = scenario_row.iloc[0]

    categorical_cols = ['Scenario Type', 'Severity', 'Affected Region', 'Affected Commodity', 'Affected Route']
    engineered_cols = [
        'Conflict Score Feature', 'Shipping Risk', 'Oil Price Change', 'Port Congestion Index',
        'Supplier Reliability', 'Inventory Buffer', 'Demand Pressure', 'Transportation Cost Index',
        'Route Availability', 'Sanction Exposure'
    ]

    df_processed, _ = scen_prep.preprocess_categorical(
        scenario_row.copy(), categorical_cols, str(models_dir), 'scenario_encoder.pkl', mode='predict', encoders=encoders
    )
    df_processed, _ = scen_feat.scale_features(
        df_processed, engineered_cols, str(models_dir), 'scenario_scaler.pkl', mode='predict', scaler=scaler
    )

    X = df_processed[engineered_cols + categorical_cols]
    prob = float(clf.predict_proba(X)[0, 1] * 100)

    name = str(row["Scenario Name"])
    parts = name.split(' ')
    if parts and parts[-1].isdigit():
        base_name = ' '.join(parts[:-1])
    else:
        base_name = name

    return {
        "scenario_id": scenario_id,
        "scenario_name": base_name,
        "scenario_type": str(row["Scenario Type"]),
        "severity": str(row["Severity"]),
        "affected_route": str(row["Affected Route"]),
        "probability": round(prob, 1)
    }


def run_scenario_effects(scenario_id: int, scenario_name: str, scenario_prob: float, risk_score: float = None) -> Dict[str, Any]:
    """Calculates downstream effects for a selected scenario without CLI interactions."""
    models_dir = SCENARIO_DIR / "models"
    data_dir = SCENARIO_DIR / "datasets"

    # Load models
    with open(models_dir / "effect_model.pkl", "rb") as f:
        reg = pickle.load(f)
    with open(models_dir / "effect_scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open(models_dir / "effect_encoder.pkl", "rb") as f:
        encoders = pickle.load(f)

    # Preprocess feature vector
    datasets = scen_prep.load_all_datasets(str(data_dir))
    if risk_score is not None:
        factor = float(risk_score) / 50.0
        for col in ['Conflict Score', 'Sanction Score', 'Port Congestion Score']:
            if col in datasets['live_risk_output'].columns:
                datasets['live_risk_output'][col] = (datasets['live_risk_output'][col] * factor).clip(0.0, 100.0)
        if 'Current Risk Score' in datasets['live_risk_output'].columns:
            datasets['live_risk_output']['Current Risk Score'] = float(risk_score)

    df = scen_feat.engineer_features(datasets)

    scenario_row = df[df['Scenario ID'] == scenario_id].copy()
    if scenario_row.empty:
        raise ValueError(f"Scenario ID {scenario_id} not found in master list.")

    categorical_cols = ['Scenario Type', 'Severity', 'Affected Region', 'Affected Commodity', 'Affected Route', 
                        'Route Status', 'Alternative Route', 'Country', 'Supplier', 'Origin', 'Destination']
    engineered_cols = [
        'Conflict Score Feature', 'Shipping Risk', 'Oil Price Change', 'Port Congestion Index',
        'Supplier Reliability', 'Inventory Buffer', 'Demand Pressure', 'Transportation Cost Index',
        'Route Availability', 'Sanction Exposure'
    ]

    scenario_processed, _ = scen_prep.preprocess_categorical(
        scenario_row.copy(), categorical_cols, str(models_dir), 'effect_encoder.pkl', mode='predict', encoders=encoders
    )
    scenario_processed, _ = scen_feat.scale_features(
        scenario_processed, engineered_cols, str(models_dir), 'effect_scaler.pkl', mode='predict', scaler=scaler
    )

    X = scenario_processed[engineered_cols + categorical_cols]
    pred = reg.predict(X)[0]

    supply_red = max(0.0, min(100.0, float(pred[0])))
    trans_cost_inc = max(0.0, min(100.0, float(pred[1])))
    est_delay = max(0.0, min(30.0, float(pred[2])))
    oil_price_inc = max(0.0, min(100.0, float(pred[3])))
    inv_red = max(0.0, min(100.0, float(pred[4])))
    dem_imp = max(0.0, min(100.0, float(pred[5])))
    supplier_avail = max(0.0, min(100.0, float(pred[6])))

    # Derived
    base_inv_days = float(scenario_row['Remaining Days'].values[0])
    inv_remaining = max(1.0, base_inv_days * (1.0 - inv_red / 100.0))
    demand_ful = max(0.0, min(100.0, 100.0 - dem_imp))

    # Overall Risk
    delay_score = (est_delay / 30.0) * 100.0
    risk_score = (
        0.20 * supply_red +
        0.15 * trans_cost_inc +
        0.15 * delay_score +
        0.15 * oil_price_inc +
        0.15 * inv_red +
        0.10 * dem_imp +
        0.10 * (100.0 - supplier_avail)
    )
    risk_label = "LOW" if risk_score <= 40 else "MEDIUM" if risk_score <= 70 else "HIGH"

    # Baseline metrics from datasets
    current_inv_val = float(scenario_row['Current Inventory'].values[0]) if 'Current Inventory' in scenario_row.columns else 2000.0
    safety_stock_val = float(scenario_row['Safety Stock'].values[0]) if 'Safety Stock' in scenario_row.columns else 500.0
    strategic_reserve_val = float(scenario_row['Strategic Reserve'].values[0]) if 'Strategic Reserve' in scenario_row.columns else 3000.0
    forecast_demand_val = float(scenario_row['Forecast Demand'].values[0]) if 'Forecast Demand' in scenario_row.columns else None
    current_demand_val = float(scenario_row['Current Demand'].values[0]) if 'Current Demand' in scenario_row.columns else None

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "affected_route": str(scenario_row['Affected Route'].values[0]),
        "route_status": str(scenario_row['Route Status'].values[0]),
        "extra_transit_time_days": int(round(scenario_row['Extra Transit Time'].values[0])),
        "supply_reduction_pct": int(round(supply_red)),
        "transportation_cost_increase_pct": int(round(trans_cost_inc)),
        "estimated_shipping_delay_days": int(round(est_delay)),
        "brent_oil_price_increase_pct": int(round(oil_price_inc)),
        "inventory_remaining_days": int(round(inv_remaining)),
        "demand_fulfillment_pct": int(round(demand_ful)),
        "supplier_availability_pct": int(round(supplier_avail)),
        "overall_risk": risk_label,
        "current_inventory": current_inv_val,
        "safety_stock": safety_stock_val,
        "strategic_reserve": strategic_reserve_val,
        "forecast_demand": forecast_demand_val,
        "current_demand": current_demand_val
    }


# ---------------------------------------------------------------------------
# 5. Alternative Supplier Module Adapter (Thread-safe absolute path files loader)
# ---------------------------------------------------------------------------
class AlternativeSupplierAdapter:
    def __init__(self):
        datasets_dir = ALTERNATIVE_DIR / "datasets"
        models_dir = ALTERNATIVE_DIR / "models"

        self.current_df = pd.read_csv(datasets_dir / "current_supplier_dataset.csv")
        self.alt_df = pd.read_csv(datasets_dir / "alternative_supplier_dataset.csv")
        self.risk_df = pd.read_csv(datasets_dir / "live_risk_dataset.csv")
        self.scenario_df = pd.read_csv(datasets_dir / "scenario_effects_dataset.csv")
        self.route_df = pd.read_csv(datasets_dir / "route_dataset.csv")
        self.delay_df = pd.read_csv(datasets_dir / "delay_dataset.csv")
        self.cost_df = pd.read_csv(datasets_dir / "cost_dataset.csv")

        self.ranker = joblib.load(models_dir / "supplier_ranker.pkl")
        self.delay_model = joblib.load(models_dir / "delay_model.pkl")
        self.cost_model = joblib.load(models_dir / "cost_model.pkl")
        self.availability_le = joblib.load(models_dir / "availability_le.pkl")
        self.delay_encoders = joblib.load(models_dir / "delay_encoders.pkl")

        # NetworkX Route optimization builder
        self.graph = nx.Graph()
        self._build_graph()

    def _build_graph(self):
        for _, row in self.route_df.iterrows():
            src = row['source_port']
            dest = row['destination_port']
            dist = row['distance_km']
            days = row['expected_transit_days']
            if self.graph.has_edge(src, dest):
                if self.graph[src][dest]['weight'] > dist:
                    self.graph.add_edge(src, dest, weight=dist, days=days)
            else:
                self.graph.add_edge(src, dest, weight=dist, days=days)

    def get_supplier_details(self, supplier_name: str) -> Dict[str, Any]:
        """
        Public interface to retrieve details for a supplier by name from either 
        alternative_supplier_dataset.csv or current_supplier_dataset.csv.
        Falls back to baseline defaults if the supplier is not found in either dataset.
        """
        row = self.alt_df[self.alt_df['supplier_name'] == supplier_name]
        if row.empty:
            row = self.current_df[self.current_df['supplier_name'] == supplier_name]
        
        if not row.empty:
            detail = row.iloc[0]
            return {
                "supplier_name": str(detail["supplier_name"]),
                "supplier_id": str(detail["supplier_id"]),
                "country": str(detail["country"]),
                "crude_type": str(detail["crude_type"]),
                "price_per_barrel": float(detail["price_per_barrel"]),
                "capacity": float(detail["capacity"]),
                "reliability": float(detail["reliability"]),
                "lead_time": int(detail["lead_time"]),
                "availability": str(detail["availability"]),
            }
            
        # Robust fallback values
        return {
            "supplier_name": supplier_name,
            "supplier_id": "UNKNOWN",
            "country": "Unknown",
            "crude_type": "Brent",
            "price_per_barrel": 80.0,
            "capacity": 100000.0,
            "reliability": 85.0,
            "lead_time": 2,
            "availability": "Medium",
        }

    def recommend_suppliers(self, current_supplier_id: str, risk_score: float = None) -> Dict[str, Any]:
        curr_supp = self.current_df[self.current_df['supplier_id'] == current_supplier_id]
        if curr_supp.empty:
            raise KeyError(f"Supplier ID {current_supplier_id} not found.")

        supp_info = curr_supp.iloc[0]

        # Scenario aggregate
        scen_info = self.scenario_df[['supply_shortage', 'production_loss', 'cost_impact']].mean()

        # Country risk
        if risk_score is None:
            country_group = self.risk_df[self.risk_df['supplier_country'] == supp_info['country']]
            if not country_group.empty:
                risk_score = round(country_group['risk_score'].mean(), 2)
                risk_level = country_group['risk_level'].mode()[0]
                disruption_probability = country_group['disruption_probability'].mode()[0]
            else:
                risk_score = round(self.risk_df['risk_score'].mean(), 2)
                risk_level = self.risk_df['risk_level'].mode()[0]
                disruption_probability = self.risk_df['disruption_probability'].mode()[0]
        else:
            risk_level = "High" if risk_score > 70 else "Medium" if risk_score > 40 else "Low"
            disruption_probability = "High" if risk_score > 70 else "Medium" if risk_score > 40 else "Low"

        prob_map = {'High': 0.9, 'Medium': 0.5, 'Low': 0.1}
        prob_val = prob_map.get(disruption_probability, 0.5)

        capacity = float(supp_info['capacity'])
        shortage_pct = (float(scen_info['supply_shortage']) / capacity) if capacity > 0 else 0
        prod_loss_pct = (float(scen_info['production_loss']) / capacity) if capacity > 0 else 0

        replacement_required = (
            risk_score > 70 or
            prob_val > 0.60 or
            shortage_pct > 0.30 or
            prod_loss_pct > 0.25
        )

        risk_assessment = {
            "Risk Score": risk_score,
            "Risk Level": risk_level,
            "Supply Shortage": f"{shortage_pct * 100:.1f}%",
            "Production Loss": f"{prod_loss_pct * 100:.1f}%",
            "Disruption Probability": f"{prob_val * 100:.1f}%",
            "Conclusion": (
                "Current supplier has HIGH RISK. Alternative supplier recommendation is required."
                if replacement_required else
                "Current supplier is operating normally. No supplier replacement is required."
            ),
        }

        # Format output mapping dictionary keys explicitly as required
        response = {
            "Current Supplier": supp_info['supplier_name'],
            "Current Supplier Country": supp_info['country'],
            "Risk Assessment": risk_assessment,
            "Decision": {
                "Replacement Required": "Yes" if replacement_required else "No"
            },
        }

        if not replacement_required:
            return response

        # Preprocess features using the loaded availability_le
        # Exclude alternatives from the current supplier's country to ensure diversity
        test_data = self.alt_df[self.alt_df['country'] != supp_info['country']].copy()
        
        # Map each alternative's country to its actual risk score
        country_risks = self.risk_df.groupby('supplier_country')['risk_score'].mean().to_dict()
        default_risk = self.risk_df['risk_score'].mean()
        test_data['risk_score'] = test_data['country'].map(lambda c: country_risks.get(c, default_risk))
        
        test_data['supply_shortage'] = float(scen_info['supply_shortage'])
        test_data['production_loss'] = float(scen_info['production_loss'])
        test_data['cost_impact'] = float(scen_info['cost_impact'])

        features = [
            'price_per_barrel', 'capacity', 'reliability', 'lead_time', 'availability',
            'risk_score', 'supply_shortage', 'production_loss', 'cost_impact'
        ]
        X_test = test_data[features].copy()
        X_test['availability'] = self.availability_le.transform(X_test['availability'])

        scores = self.ranker.predict(X_test)
        test_data['ranking_score'] = scores
        top_4 = test_data.sort_values(by='ranking_score', ascending=False).head(4)

        alternatives = []
        for i, row in enumerate(top_4.itertuples(), 1):
            reasons = []
            if float(row.reliability) > 90: reasons.append("High Reliability")
            if float(row.price_per_barrel) < float(supp_info['price_per_barrel']): reasons.append("Lower Price than current")
            if float(row.capacity) > float(supp_info['capacity']): reasons.append("Higher Capacity")
            if int(row.lead_time) < 15: reasons.append("Low Lead Time")
            if not reasons: reasons.append("Optimal balance of features")

            alternatives.append({
                "rank": i,
                "supplier_id": row.supplier_id,
                "supplier_name": row.supplier_name,
                "country": row.country,
                "ranking_score": float(row.ranking_score),
                "Reason": ", ".join(reasons),
            })

        response["Top 4 Ranked Suppliers"] = alternatives
        return response

    def analyze_route(self, selected_supplier: str) -> Dict[str, Any]:
        row = self.route_df[self.route_df['supplier_name'] == selected_supplier]
        if row.empty:
            idx = hash(selected_supplier) % len(self.route_df)
            best = self.route_df.iloc[idx]
            src = best['source_port']
            dest = best['destination_port']
        else:
            best = row.loc[row['distance_km'].idxmin()]
            src = best['source_port']
            dest = best['destination_port']

        if src not in self.graph or dest not in self.graph:
            if not row.empty:
                best = row.loc[row['distance_km'].idxmin()]
                return {
                    "Best Route": f"{best['source_port']} -> {best['destination_port']}",
                    "Distance": float(best['distance_km']),
                    "Expected Delivery": int(best['expected_transit_days'])
                }
            raise KeyError(f"Graph nodes not found for ports: {src} -> {dest}")

        try:
            path = nx.dijkstra_path(self.graph, src, dest, weight='weight')
            total_dist = 0
            total_days = 0
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                total_dist += self.graph[u][v]['weight']
                total_days += self.graph[u][v]['days']
            return {
                "Best Route": ' -> '.join(path),
                "Distance": total_dist,
                "Expected Delivery": total_days
            }
        except nx.NetworkXNoPath:
            if not row.empty:
                best = row.loc[row['distance_km'].idxmin()]
                return {
                    "Best Route": f"{best['source_port']} -> {best['destination_port']}",
                    "Distance": float(best['distance_km']),
                    "Expected Delivery": int(best['expected_transit_days'])
                }
            raise RuntimeError(f"No path between {src} and {dest}")

    def predict_delay(self, selected_supplier: str) -> Dict[str, Any]:
        row = self.delay_df[self.delay_df['route_name'] == selected_supplier]
        if not row.empty:
            best = row.iloc[0]
            dist = float(best['distance_km'])
            weather, cong, geo = best['weather_level'], best['port_congestion'], best['geopolitical_risk']
        else:
            # Use a deterministic index based on supplier name hash so each
            # supplier always gets a unique, consistent row from the dataset.
            idx = hash(selected_supplier) % len(self.delay_df)
            best = self.delay_df.iloc[idx]
            dist = float(best['distance_km'])
            weather, cong, geo = best['weather_level'], best['port_congestion'], best['geopolitical_risk']

        input_df = pd.DataFrame([{
            'distance_km': dist,
            'weather_level': weather,
            'port_congestion': cong,
            'geopolitical_risk': geo
        }])

        X = input_df.copy()
        categorical_cols = ['weather_level', 'port_congestion', 'geopolitical_risk']
        for col in categorical_cols:
            le = self.delay_encoders[col]
            X[col] = X[col].map(lambda s: le.transform([s])[0] if s in le.classes_ else -1)

        pred_delay = self.delay_model.predict(X)[0]
        exp_delivery = max(2, int(dist) // 400)
        actual = exp_delivery + max(0, int(round(pred_delay)))

        return {
            "Predicted Delay": f"{max(0, int(round(pred_delay)))} Days",
            "Actual Delivery": f"{actual} Days"
        }

    def predict_cost(self, selected_supplier: str) -> Dict[str, Any]:
        row = self.cost_df[self.cost_df['route_name'] == selected_supplier]
        if not row.empty:
            best = row.iloc[0]
            dist = float(best['distance_km'])
            trans = float(best['transportation_cost'])
            ins = float(best['insurance_cost'])
            fuel = float(best['fuel_cost'])
            log = float(best['logistics_cost'])
        else:
            idx = hash(selected_supplier) % len(self.cost_df)
            best = self.cost_df.iloc[idx]
            dist = float(best['distance_km'])
            trans = float(best['transportation_cost'])
            ins = float(best['insurance_cost'])
            fuel = float(best['fuel_cost'])
            log = float(best['logistics_cost'])

        X = pd.DataFrame([{
            'distance_km': dist,
            'transportation_cost': trans,
            'insurance_cost': ins,
            'fuel_cost': fuel,
            'logistics_cost': log
        }])

        pred_total = self.cost_model.predict(X)[0]

        return {
            "Transportation Cost": f"${trans:,.2f}",
            "Insurance Cost": f"${ins:,.2f}",
            "Fuel Cost": f"${fuel:,.2f}",
            "Logistics Cost": f"${log:,.2f}",
            "Predicted Total Cost": f"${pred_total:,.2f}"
        }


# Global instances to avoid reloading datasets repeatedly
_supplier_adapter = None

def get_supplier_adapter() -> AlternativeSupplierAdapter:
    global _supplier_adapter
    if _supplier_adapter is None:
        _supplier_adapter = AlternativeSupplierAdapter()
    return _supplier_adapter


# ---------------------------------------------------------------------------
# Helpers for Strategic Reserve Optimizer Integration (Decoupled Data Fetching)
# ---------------------------------------------------------------------------
def get_refinery_demands(horizon_days: int) -> List[Dict[str, Any]]:
    """
    Loads daily refinery demands from daily_refinery_demand.csv dataset and
    returns the data structure mapped to standard refinery priorities.
    """
    csv_path = STRATEGIC_DIR / "data" / "raw" / "daily_refinery_demand.csv"
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            # Fetch first horizon_days rows
            rows = df.head(horizon_days)
            return [
                {
                    "id": "Refinery_A",
                    "daily_demand": [float(val) for val in rows["RIL_Jamnagar_demand_kmt"].tolist()],
                    "priority": 2.0
                },
                {
                    "id": "Refinery_B",
                    "daily_demand": [float(val) for val in rows["IOCL_Panipat_demand_kmt"].tolist()],
                    "priority": 1.5
                },
                {
                    "id": "Refinery_C",
                    "daily_demand": [float(val) for val in rows["MRPL_Mangaluru_demand_kmt"].tolist()],
                    "priority": 1.0
                }
            ]
        except Exception as e:
            logger.warning(f"Failed to load refinery demands from CSV: {e}")

    # Fallback to standard baseline defaults
    return [
        {"id": "Refinery_A", "daily_demand": [100.0] * horizon_days, "priority": 2.0},
        {"id": "Refinery_B", "daily_demand": [80.0] * horizon_days, "priority": 1.5},
        {"id": "Refinery_C", "daily_demand": [50.0] * horizon_days, "priority": 1.0}
    ]


def get_expected_incoming_shipments(horizon_days: int) -> List[float]:
    """
    Loads shipping delays or AIS vessel data to determine incoming shipments,
    falling back to standard defaults.
    """
    # Look at shipping ais dataset if available to get tanker movements average
    csv_path = RISK_DIR / "datasets" / "shipping_ais_dataset.csv"
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            avg_movements = float(df["tanker_movements"].mean())
            # Scale shipments dynamically based on AIS data (normalized to ~5.0 units)
            base_shipment = round(avg_movements / 6.6, 1) # e.g. 33 / 6.6 = 5.0
            return [base_shipment] * horizon_days
        except Exception as e:
            logger.warning(f"Failed to load expected shipments from AIS dataset: {e}")

    return [5.0] * horizon_days


def get_base_supply_gap(forecast_demand: float = None, current_demand: float = None) -> float:
    """
    Retrieves or calculates the base supply gap. Uses demand forecast differences if available,
    falling back to 20.0.
    """
    if forecast_demand is not None and current_demand is not None:
        gap = forecast_demand - current_demand
        if gap > 0:
            # Scale to a daily gap format (e.g. division factor to match typical 20.0 magnitude)
            return round(min(50.0, max(5.0, gap / 10.0)), 2)
    return 20.0


# ---------------------------------------------------------------------------
# 6. Strategic Reserve Optimizer Adapter (GIL-safe, no runtime path updates)
# ---------------------------------------------------------------------------
def run_strategic_optimization(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Runs the daily SPR Optimization agent."""
    agent = StrategicReserveAgent()
    return agent.optimize(input_data)
