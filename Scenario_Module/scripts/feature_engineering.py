import os
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

def engineer_features(datasets):
    # Retrieve each dataset
    sm = datasets['scenario_master']
    dr = datasets['disruption_rules']
    sr = datasets['shipping_routes']
    op = datasets['oil_price_dataset']
    sc = datasets['supplier_capacity']
    il = datasets['inventory_levels']
    tc = datasets['transportation_cost']
    df_fc = datasets['demand_forecast']
    lr = datasets['live_risk_output']
    
    # Merge step-by-step on 'Scenario ID'
    df = sm.merge(dr, on='Scenario ID', how='left')
    df = df.merge(sr, on='Scenario ID', how='left', suffixes=('', '_sr'))
    df = df.merge(op, on='Scenario ID', how='left')
    df = df.merge(sc, on='Scenario ID', how='left')
    df = df.merge(il, on='Scenario ID', how='left')
    df = df.merge(tc, on='Scenario ID', how='left', suffixes=('', '_tc'))
    df = df.merge(df_fc, on='Scenario ID', how='left')
    df = df.merge(lr, on='Scenario ID', how='left')
    
    # Compute the 10 custom engineered features
    # 1. Conflict Score
    sev_weight = df['Severity'].map({'Critical': 1.2, 'High': 1.0, 'Medium': 0.8}).fillna(1.0)
    df['Conflict Score Feature'] = (df['Conflict Score'].fillna(0.0) * sev_weight).round(3)
    
    # 2. Shipping Risk
    status_risk = df['Route Status'].map({'Closed': 1.0, 'Restricted': 0.5, 'Open': 0.1}).fillna(0.1)
    df['Shipping Risk'] = ((df['Distance'].fillna(5000.0) / 12000.0) * status_risk).round(3)
    
    # 3. Oil Price Change
    df['Oil Price Change'] = df['Price Change %'].fillna(0.0).round(3)
    
    # 4. Port Congestion Index
    df['Port Congestion Index'] = df['Port Congestion Score'].fillna(0.0).round(3)
    
    # 5. Supplier Reliability
    df['Supplier Reliability'] = (df['Reliability'].fillna(85.0) / 100.0).round(3)
    
    # 6. Inventory Buffer
    df['Inventory Buffer'] = (df['Current Inventory'] / (df['Safety Stock'] + 1e-5)).fillna(1.0).round(3)
    
    # 7. Demand Pressure
    total_inv = df['Strategic Reserve'].fillna(0.0) + df['Current Inventory'].fillna(0.0)
    df['Demand Pressure'] = (df['Forecast Demand'] / (total_inv + 1e-5)).fillna(1.0).round(3)
    
    # 8. Transportation Cost Index
    df['Transportation Cost Index'] = (df['Total Cost'] / (df['Distance'] + 1e-5)).fillna(0.0).round(3)
    
    # 9. Route Availability
    df['Route Availability'] = df['Route Status'].map({'Closed': 0.0, 'Restricted': 0.5, 'Open': 1.0}).fillna(1.0)
    
    # 10. Sanction Exposure
    type_weight = df['Scenario Type'].map({'Sanctions': 1.2, 'Geopolitical Conflict': 1.0}).fillna(0.5)
    df['Sanction Exposure'] = (df['Sanction Score'].fillna(0.0) * type_weight).round(3)
    
    return df

def scale_features(df, feature_cols, models_dir, filename, mode='train', scaler=None):
    os.makedirs(models_dir, exist_ok=True)
    filepath = os.path.join(models_dir, filename)
    
    if mode == 'train':
        scaler = StandardScaler()
        df[feature_cols] = scaler.fit_transform(df[feature_cols])
        with open(filepath, 'wb') as f:
            pickle.dump(scaler, f)
        return df, scaler
    else:
        if scaler is None:
            with open(filepath, 'rb') as f:
                scaler = pickle.load(f)
        df[feature_cols] = scaler.transform(df[feature_cols])
        return df, scaler
