from flask import Blueprint, jsonify, request
import pandas as pd
import joblib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.route_optimizer import RouteOptimizer
from utils.preprocessing import preprocess_delay_data

analysis_bp = Blueprint('analysis_bp', __name__)

route_opt = RouteOptimizer()

try:
    delay_model = joblib.load('models/delay_model.pkl')
    cost_model = joblib.load('models/cost_model.pkl')
except Exception as e:
    print(f"Error loading analysis models: {e}")

# ---------------------------------------------------------------------------
# Load datasets once at module start (deterministic reads)
# ---------------------------------------------------------------------------
try:
    route_df = pd.read_csv('datasets/route_dataset.csv')
    delay_df = pd.read_csv('datasets/delay_dataset.csv')
    cost_df  = pd.read_csv('datasets/cost_dataset.csv')
except Exception as e:
    print(f"Error loading analysis datasets: {e}")

# ---------------------------------------------------------------------------
# Pre-compute deterministic scenario and delay aggregates
# Used as fallbacks when a supplier name has no exact match in the dataset
# ---------------------------------------------------------------------------
_route_mean_dist  = route_df['distance_km'].mean()
_route_mean_days  = route_df['expected_transit_days'].mean()

_delay_global = {
    'distance_km':      delay_df['distance_km'].mean(),
    'weather_level':    delay_df['weather_level'].mode()[0],
    'port_congestion':  delay_df['port_congestion'].mode()[0],
    'geopolitical_risk': delay_df['geopolitical_risk'].mode()[0],
}

_cost_global = {
    'distance_km':         cost_df['distance_km'].mean(),
    'transportation_cost': cost_df['transportation_cost'].mean(),
    'insurance_cost':      cost_df['insurance_cost'].mean(),
    'fuel_cost':           cost_df['fuel_cost'].mean(),
    'logistics_cost':      cost_df['logistics_cost'].mean(),
}


@analysis_bp.route('/route', methods=['POST'])
def analyze_route():
    data = request.json
    selected_supplier = data.get('selected_supplier')
    if not selected_supplier:
        return jsonify({"error": "selected_supplier required"}), 400

    # Look up the supplier's row in route_dataset by supplier_name
    row = route_df[route_df['supplier_name'] == selected_supplier]

    if row.empty:
        # Fallback: use global mean distance/days and find a valid path
        src  = route_df['source_port'].mode()[0]
        dest = route_df['destination_port'].mode()[0]
    else:
        best = row.loc[row['distance_km'].idxmin()]
        src  = best['source_port']
        dest = best['destination_port']

    path, dist, days = route_opt.find_best_route(src, dest)

    if not path:
        # src == dest or no path — return the dataset values directly
        if not row.empty:
            best = row.loc[row['distance_km'].idxmin()]
            return jsonify({
                "Best Route": f"{best['source_port']} -> {best['destination_port']}",
                "Distance": float(best['distance_km']),
                "Expected Delivery": int(best['expected_transit_days'])
            })
        return jsonify({"error": "Route not found"}), 404

    return jsonify({
        "Best Route": ' -> '.join(path),
        "Distance": dist,
        "Expected Delivery": days
    })


@analysis_bp.route('/delay', methods=['POST'])
def predict_delay():
    data = request.json
    selected_supplier = data.get('selected_supplier')

    # Look up the supplier's delay features from delay_dataset
    # delay_dataset uses route_name; match supplier name to route_name
    row = delay_df[delay_df['route_name'] == selected_supplier]

    if not row.empty:
        best = row.iloc[0]
        dist    = float(best['distance_km'])
        weather = best['weather_level']
        cong    = best['port_congestion']
        geo     = best['geopolitical_risk']
    else:
        # Fallback: use global mode/mean values — still fully deterministic
        dist    = _delay_global['distance_km']
        weather = _delay_global['weather_level']
        cong    = _delay_global['port_congestion']
        geo     = _delay_global['geopolitical_risk']

    input_df = pd.DataFrame([{
        'distance_km':       dist,
        'weather_level':     weather,
        'port_congestion':   cong,
        'geopolitical_risk': geo
    }])

    X, _ = preprocess_delay_data(input_df, is_training=False)
    pred_delay = delay_model.predict(X)[0]

    exp_delivery = max(2, int(dist) // 400)
    actual = exp_delivery + max(0, int(round(pred_delay)))

    return jsonify({
        "Predicted Delay":  f"{max(0, int(round(pred_delay)))} Days",
        "Actual Delivery":  f"{actual} Days"
    })


@analysis_bp.route('/cost', methods=['POST'])
def predict_cost():
    data = request.json
    selected_supplier = data.get('selected_supplier')

    # Look up the supplier's cost features from cost_dataset
    row = cost_df[cost_df['route_name'] == selected_supplier]

    if not row.empty:
        best  = row.iloc[0]
        dist  = float(best['distance_km'])
        trans = float(best['transportation_cost'])
        ins   = float(best['insurance_cost'])
        fuel  = float(best['fuel_cost'])
        log   = float(best['logistics_cost'])
    else:
        # Fallback: use global mean values — still fully deterministic
        dist  = _cost_global['distance_km']
        trans = _cost_global['transportation_cost']
        ins   = _cost_global['insurance_cost']
        fuel  = _cost_global['fuel_cost']
        log   = _cost_global['logistics_cost']

    X = pd.DataFrame([{
        'distance_km':         dist,
        'transportation_cost': trans,
        'insurance_cost':      ins,
        'fuel_cost':           fuel,
        'logistics_cost':      log
    }])

    pred_total = cost_model.predict(X)[0]

    return jsonify({
        "Transportation Cost":  f"${trans:,.2f}",
        "Insurance Cost":       f"${ins:,.2f}",
        "Fuel Cost":            f"${fuel:,.2f}",
        "Logistics Cost":       f"${log:,.2f}",
        "Predicted Total Cost": f"${pred_total:,.2f}"
    })


@analysis_bp.route('/complete-analysis', methods=['POST'])
def complete_analysis():
    data = request.json
    current_id        = data.get('current_supplier_id')
    selected_supplier = data.get('selected_supplier')

    if not current_id or not selected_supplier:
        return jsonify({"error": "current_supplier_id and selected_supplier required"}), 400

    from flask import current_app

    with current_app.test_client() as client:
        # 1. Recommend & Risk Assessment
        rec_res = client.post('/recommend', json={"current_supplier_id": current_id}).get_json()
        if "error" in rec_res:
            return jsonify(rec_res), 400

        # Check Decision
        decision = rec_res.get("Decision", {})
        if decision.get("Replacement Required") == "No":
            return jsonify({
                "Current Supplier":         rec_res.get("Current Supplier"),
                "Current Supplier Country": rec_res.get("Current Supplier Country"),
                "Risk Assessment":          rec_res.get("Risk Assessment"),
                "Decision":                 decision,
                "Final Recommendation":     "Current supplier is safe. No alternative supplier recommendation. Processing stopped."
            })

        # 2. Route
        route_res = client.post('/route', json={"selected_supplier": selected_supplier}).get_json()

        # 3. Delay
        delay_res = client.post('/delay', json={"selected_supplier": selected_supplier}).get_json()

        # 4. Cost
        cost_res = client.post('/cost', json={"selected_supplier": selected_supplier}).get_json()

    return jsonify({
        "Current Supplier":         rec_res.get("Current Supplier"),
        "Current Supplier Country": rec_res.get("Current Supplier Country"),
        "Risk Assessment":          rec_res.get("Risk Assessment"),
        "Decision":                 decision,
        "Top Ranked Suppliers":     rec_res.get("Top 4 Ranked Suppliers"),
        "Selected Supplier":        selected_supplier,
        "Best Route":               route_res.get("Best Route"),
        "Shortest Distance":        f"{route_res.get('Distance')} km",
        "Expected Delivery":        f"{route_res.get('Expected Delivery')} Days",
        "Predicted Delay":          delay_res.get("Predicted Delay"),
        "Actual Delivery":          delay_res.get("Actual Delivery"),
        "Transportation Cost":      cost_res.get("Transportation Cost"),
        "Insurance Cost":           cost_res.get("Insurance Cost"),
        "Fuel Cost":                cost_res.get("Fuel Cost"),
        "Logistics Cost":           cost_res.get("Logistics Cost"),
        "Predicted Total Cost":     cost_res.get("Predicted Total Cost"),
        "Final Recommendation":     f"Proceed with {selected_supplier} via {route_res.get('Best Route')}."
    })
