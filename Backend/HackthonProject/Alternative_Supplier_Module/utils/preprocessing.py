import pandas as pd
from sklearn.preprocessing import LabelEncoder
import joblib

def preprocess_supplier_data(df, is_training=False):
    features = [
        'price_per_barrel', 'capacity', 'reliability', 
        'lead_time', 'availability', 'risk_score', 
        'supply_shortage', 'production_loss', 'cost_impact'
    ]
    
    if is_training:
        # Assuming df has all features
        X = df[features].copy()
        y = df['supplier_rank'].copy() if 'supplier_rank' in df.columns else None
    else:
        X = df[features].copy()
        y = None
        
    # Handle categorical variable 'availability'
    if is_training:
        le = LabelEncoder()
        X['availability'] = le.fit_transform(X['availability'])
        joblib.dump(le, 'models/availability_le.pkl')
    else:
        try:
            le = joblib.load('models/availability_le.pkl')
            X['availability'] = le.transform(X['availability'])
        except Exception:
            # Fallback if label encoder not found
            le = LabelEncoder()
            X['availability'] = le.fit_transform(X['availability'])
            
    return X, y

def preprocess_delay_data(df, is_training=False):
    features = ['distance_km', 'weather_level', 'port_congestion', 'geopolitical_risk']
    
    X = df[features].copy()
    y = df['delay_days'].copy() if is_training and 'delay_days' in df.columns else None
    
    categorical_cols = ['weather_level', 'port_congestion', 'geopolitical_risk']
    
    if is_training:
        encoders = {}
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col])
            encoders[col] = le
        joblib.dump(encoders, 'models/delay_encoders.pkl')
    else:
        try:
            encoders = joblib.load('models/delay_encoders.pkl')
            for col in categorical_cols:
                if col in encoders:
                    # Handle unseen labels gracefully if necessary
                    X[col] = X[col].map(lambda s: encoders[col].transform([s])[0] if s in encoders[col].classes_ else -1)
        except Exception:
            pass
            
    return X, y
