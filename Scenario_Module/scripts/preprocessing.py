import os
import pickle
import pandas as pd
from sklearn.preprocessing import LabelEncoder

def preprocess_categorical(df, cols, models_dir, filename, mode='train', encoders=None):
    os.makedirs(models_dir, exist_ok=True)
    filepath = os.path.join(models_dir, filename)
    
    if mode == 'train':
        saved_encoders = {}
        for col in cols:
            if col in df.columns:
                le = LabelEncoder()
                df[col] = df[col].astype(str).fillna('missing')
                df[col] = le.fit_transform(df[col])
                saved_encoders[col] = le
        with open(filepath, 'wb') as f:
            pickle.dump(saved_encoders, f)
        return df, saved_encoders
    else:
        if encoders is None:
            with open(filepath, 'rb') as f:
                encoders = pickle.load(f)
        for col in cols:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna('missing')
                le = encoders.get(col)
                if le is not None:
                    # Handle unseen labels
                    classes = le.classes_.tolist()
                    df[col] = df[col].apply(lambda x: x if x in classes else classes[0])
                    df[col] = le.transform(df[col])
        return df, encoders

def load_all_datasets(data_dir):
    datasets = {}
    files = [
        'scenario_master.csv', 'disruption_rules.csv', 'shipping_routes.csv',
        'oil_price_dataset.csv', 'supplier_capacity.csv', 'inventory_levels.csv',
        'transportation_cost.csv', 'demand_forecast.csv', 'live_risk_output.csv'
    ]
    for filename in files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            datasets[filename.split('.')[0]] = pd.read_csv(filepath)
        else:
            raise FileNotFoundError(f"Required dataset {filename} not found at {filepath}")
    return datasets
