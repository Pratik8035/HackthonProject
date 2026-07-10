import os
import pickle
import numpy as np
from preprocessing import load_all_datasets, preprocess_categorical
from feature_engineering import engineer_features, scale_features

def run_effect_prediction(base_dir, scenario_id, scenario_name, scenario_prob):
    data_dir = os.path.join(base_dir, 'datasets')
    models_dir = os.path.join(base_dir, 'models')
    
    # 1. Load trained model, scaler, and encoders
    with open(os.path.join(models_dir, 'effect_model.pkl'), 'rb') as f:
        reg = pickle.load(f)
    with open(os.path.join(models_dir, 'effect_scaler.pkl'), 'rb') as f:
        scaler = pickle.load(f)
    with open(os.path.join(models_dir, 'effect_encoder.pkl'), 'rb') as f:
        encoders = pickle.load(f)
        
    # 2. Get specific scenario feature vector
    datasets = load_all_datasets(data_dir)
    df = engineer_features(datasets)
    
    # Filter for selected scenario_id
    scenario_row = df[df['Scenario ID'] == scenario_id].copy()
    
    # Preprocess
    categorical_cols = ['Scenario Type', 'Severity', 'Affected Region', 'Affected Commodity', 'Affected Route', 'Route Status', 'Alternative Route', 'Country', 'Supplier', 'Origin', 'Destination']
    engineered_cols = [
        'Conflict Score Feature',
        'Shipping Risk',
        'Oil Price Change',
        'Port Congestion Index',
        'Supplier Reliability',
        'Inventory Buffer',
        'Demand Pressure',
        'Transportation Cost Index',
        'Route Availability',
        'Sanction Exposure'
    ]
    
    # Preprocess categorical using saved encoders
    scenario_processed, _ = preprocess_categorical(scenario_row.copy(), categorical_cols, models_dir, 'effect_encoder.pkl', mode='predict', encoders=encoders)
    
    # Scale numerical using saved scaler
    scenario_processed, _ = scale_features(scenario_processed, engineered_cols, models_dir, 'effect_scaler.pkl', mode='predict', scaler=scaler)
    
    X_cols = engineered_cols + categorical_cols
    X = scenario_processed[X_cols]
    
    # 3. Predict the 7 impact metrics
    pred = reg.predict(X)[0]
    
    supply_red = float(pred[0])
    trans_cost_inc = float(pred[1])
    est_delay = float(pred[2])
    oil_price_inc = float(pred[3])
    inv_red = float(pred[4])
    dem_imp = float(pred[5])
    supplier_avail = float(pred[6])
    
    # Clip to realistic ranges
    supply_red = max(0.0, min(100.0, supply_red))
    trans_cost_inc = max(0.0, min(100.0, trans_cost_inc))
    est_delay = max(0.0, min(30.0, est_delay))
    oil_price_inc = max(0.0, min(100.0, oil_price_inc))
    inv_red = max(0.0, min(100.0, inv_red))
    dem_imp = max(0.0, min(100.0, dem_imp))
    supplier_avail = max(0.0, min(100.0, supplier_avail))
    
    # Derived impacts
    # Inventory Remaining (Days) - base inventory remaining minus reduction ratio
    base_inv_days = float(scenario_row['Remaining Days'].values[0])
    inv_remaining = max(1.0, base_inv_days * (1.0 - inv_red / 100.0))
    
    # Demand Fulfillment (%) = 100 - Demand Impact (%)
    demand_ful = max(0.0, min(100.0, 100.0 - dem_imp))
    
    # 4. Calculate Overall Risk Score
    # Normalized sub-scores
    delay_score = (est_delay / 30.0) * 100.0
    inv_loss_score = inv_red
    demand_loss_score = dem_imp
    supplier_loss_score = 100.0 - supplier_avail
    
    risk_score = (
        0.20 * supply_red +
        0.15 * trans_cost_inc +
        0.15 * delay_score +
        0.15 * oil_price_inc +
        0.15 * inv_loss_score +
        0.10 * demand_loss_score +
        0.10 * supplier_loss_score
    )
    
    if risk_score <= 40:
        risk_label = "LOW"
    elif risk_score <= 70:
        risk_label = "MEDIUM"
    else:
        risk_label = "HIGH"
        
    # Clean the printed scenario name
    clean_name = scenario_name
    if ' ' in clean_name:
        parts = clean_name.split(' ')
        if parts[-1].isdigit():
            clean_name = ' '.join(parts[:-1])

    # 5. Display formatted report EXACTLY as required
    print("\n========================================================")
    print("EFFECTS CALCULATION")
    print("========================================================")
    print(f"\nSelected Scenario\n")
    print(f"{clean_name}")
    print("\n------------------------------------------------\n")
    print(f"{'Affected Route':<30} {scenario_row['Affected Route'].values[0]}")
    print(f"{'Route Status':<30} {scenario_row['Route Status'].values[0]}")
    print(f"{'Additional Transit Time':<30} {int(round(scenario_row['Extra Transit Time'].values[0]))} Days")
    print(f"{'Supply Reduction':<30} {int(round(supply_red))}%")
    print(f"{'Transportation Cost Increase':<30} {int(round(trans_cost_inc))}%")
    print(f"{'Estimated Shipping Delay':<30} {int(round(est_delay))} Days")
    print(f"{'Brent Oil Price Increase':<30} {int(round(oil_price_inc))}%")
    print(f"{'Inventory Remaining':<30} {int(round(inv_remaining))} Days")
    print(f"{'Demand Fulfillment':<30} {int(round(demand_ful))}%")
    print(f"{'Supplier Availability':<30} {int(round(supplier_avail))}%")
    print(f"{'Overall Risk':<30} {risk_label}")
    print("\n========================================================")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_effect_prediction(base_dir, 1, "Mock Scenario", 50.0)
