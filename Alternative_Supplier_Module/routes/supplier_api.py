from flask import Blueprint, jsonify, request
import pandas as pd
import numpy as np
import joblib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.preprocessing import preprocess_supplier_data
from utils.route_optimizer import RouteOptimizer

supplier_bp = Blueprint('supplier_bp', __name__)

# ---------------------------------------------------------------------------
# Load datasets once at module start (deterministic reads)
# ---------------------------------------------------------------------------
try:
    current_df  = pd.read_csv('datasets/current_supplier_dataset.csv')
    alt_df      = pd.read_csv('datasets/alternative_supplier_dataset.csv')
    risk_df     = pd.read_csv('datasets/live_risk_dataset.csv')
    scenario_df = pd.read_csv('datasets/scenario_effects_dataset.csv')
except Exception as e:
    print(f"Error loading datasets: {e}")

try:
    ranker = joblib.load('models/supplier_ranker.pkl')
except Exception as e:
    print(f"Error loading ranker model: {e}")

# ---------------------------------------------------------------------------
# Pre-compute deterministic scenario-effect aggregates (global mean)
# Replaces scenario_df.sample(1) — same value on every request
# ---------------------------------------------------------------------------
_scen_agg = scenario_df[['supply_shortage', 'production_loss', 'cost_impact']].mean()

# ---------------------------------------------------------------------------
# Pre-compute per-country risk aggregates (mean risk_score, mode level/prob)
# Replaces risk_df.sample(1) and risk_df.iloc[0] on unfiltered frame
# ---------------------------------------------------------------------------
def _build_risk_agg(df):
    """Return {country: {risk_score, risk_level, disruption_probability}} from CSV."""
    agg = {}
    for country, group in df.groupby('supplier_country'):
        agg[country] = {
            'risk_score':             round(group['risk_score'].mean(), 2),
            'risk_level':             group['risk_level'].mode()[0],
            'disruption_probability': group['disruption_probability'].mode()[0],
        }
    return agg

_risk_agg = _build_risk_agg(risk_df)

# Global fallback when the supplier's country is not in live_risk_dataset
_global_risk = {
    'risk_score':             round(risk_df['risk_score'].mean(), 2),
    'risk_level':             risk_df['risk_level'].mode()[0],
    'disruption_probability': risk_df['disruption_probability'].mode()[0],
}


@supplier_bp.route('/current-suppliers', methods=['GET'])
def get_current_suppliers():
    return jsonify(current_df.to_dict(orient='records'))


@supplier_bp.route('/recommend', methods=['POST'])
def recommend_suppliers():
    data = request.json
    current_id = data.get('current_supplier_id')

    if not current_id:
        return jsonify({"error": "current_supplier_id required"}), 400

    curr_supp = current_df[current_df['supplier_id'] == current_id]
    if curr_supp.empty:
        return jsonify({"error": "Supplier not found"}), 404

    supp_info = curr_supp.iloc[0]

    # Fetch Live Risk data — deterministic mean per country
    risk_info = _risk_agg.get(supp_info['country'], _global_risk)

    # Fetch Scenario Effects — deterministic global mean (no .sample())
    scen_info = _scen_agg

    # Compute disruption probability numeric value
    prob_map = {'High': 0.9, 'Medium': 0.5, 'Low': 0.1}
    prob_val = prob_map.get(risk_info['disruption_probability'], 0.5)

    # Calculate percentages
    capacity      = float(supp_info['capacity'])
    shortage_pct  = (float(scen_info['supply_shortage'])  / capacity) if capacity > 0 else 0
    prod_loss_pct = (float(scen_info['production_loss'])  / capacity) if capacity > 0 else 0

    risk_score = float(risk_info['risk_score'])

    # Determine if replacement is required
    replacement_required = (
        risk_score > 70 or
        prob_val > 0.60 or
        shortage_pct > 0.30 or
        prod_loss_pct > 0.25
    )

    risk_assessment = {
        "Risk Score":             risk_score,
        "Risk Level":             risk_info['risk_level'],
        "Supply Shortage":        f"{shortage_pct * 100:.1f}%",
        "Production Loss":        f"{prod_loss_pct * 100:.1f}%",
        "Disruption Probability": f"{prob_val * 100:.1f}%",
        "Conclusion": (
            "Current supplier has HIGH RISK. Alternative supplier recommendation is required."
            if replacement_required else
            "Current supplier is operating normally. No supplier replacement is required."
        ),
    }

    response = {
        "Current Supplier":         supp_info['supplier_name'],
        "Current Supplier Country": supp_info['country'],
        "Risk Assessment":          risk_assessment,
        "Decision": {
            "Replacement Required": "Yes" if replacement_required else "No"
        },
    }

    if not replacement_required:
        return jsonify(response)

    # Supplier Ranking
    test_data = alt_df.copy()
    test_data['risk_score']      = risk_score
    test_data['supply_shortage'] = float(scen_info['supply_shortage'])
    test_data['production_loss'] = float(scen_info['production_loss'])
    test_data['cost_impact']     = float(scen_info['cost_impact'])

    X_test, _ = preprocess_supplier_data(test_data, is_training=False)

    scores = ranker.predict(X_test)
    test_data['ranking_score'] = scores

    top_4 = test_data.sort_values(by='ranking_score', ascending=False).head(4)

    alternatives = []
    for i, row in enumerate(top_4.itertuples(), 1):
        reasons = []
        if float(row.reliability) > 90:
            reasons.append("High Reliability")
        if float(row.price_per_barrel) < float(supp_info['price_per_barrel']):
            reasons.append("Lower Price than current")
        if float(row.capacity) > float(supp_info['capacity']):
            reasons.append("Higher Capacity")
        if int(row.lead_time) < 15:
            reasons.append("Low Lead Time")

        if not reasons:
            reasons.append("Optimal balance of features")

        alternatives.append({
            "rank":          i,
            "supplier_id":   row.supplier_id,
            "supplier_name": row.supplier_name,
            "country":       row.country,
            "ranking_score": float(row.ranking_score),
            "Reason":        ", ".join(reasons),
        })

    response["Top 4 Ranked Suppliers"] = alternatives
    return jsonify(response)
