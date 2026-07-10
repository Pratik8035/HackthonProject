import os
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from preprocessing import load_all_datasets, preprocess_categorical
from feature_engineering import engineer_features, scale_features

def train_effect_regressor(base_dir):
    data_dir = os.path.join(base_dir, 'datasets')
    models_dir = os.path.join(base_dir, 'models')
    
    # 1. Load datasets
    datasets = load_all_datasets(data_dir)
    
    # Merge and build features
    df = engineer_features(datasets)
    
    # Preprocess categoricals (mode='train' fits and saves encoders for effect model)
    categorical_cols = ['Scenario Type', 'Severity', 'Affected Region', 'Affected Commodity', 'Affected Route', 'Route Status', 'Alternative Route', 'Country', 'Supplier', 'Origin', 'Destination']
    df, encoders = preprocess_categorical(df, categorical_cols, models_dir, 'effect_encoder.pkl', mode='train')
    
    # Define features (the 10 engineered features)
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
    
    X_cols = engineered_cols + categorical_cols
    
    # Define 7 targets for effect predictions
    y_cols = [
        'Supply Reduction %',
        'Transportation Cost Increase %',
        'Expected Delay',
        'Oil Price Increase %',
        'Inventory Reduction %',
        'Demand Impact %',
        'Supplier Availability %'
    ]
    
    # Scale features (mode='train' fits and saves effect_scaler.pkl)
    df, scaler = scale_features(df, engineered_cols, models_dir, 'effect_scaler.pkl', mode='train')
    
    X = df[X_cols]
    y = df[y_cols]
    
    # Split train/test (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train RandomForestRegressor
    reg = RandomForestRegressor(n_estimators=100, random_state=42)
    reg.fit(X_train, y_train)
    
    # Evaluate
    y_pred = reg.predict(X_test)

    # Initialize metric accumulators
    avg_mae = 0.0
    avg_rmse = 0.0
    avg_r2 = 0.0
    # Compute metrics for each target column
    for i, col_name in enumerate(y_cols):
        col_test = y_test.iloc[:, i]
        col_pred = y_pred[:, i]
        avg_mae += mean_absolute_error(col_test, col_pred)
        avg_rmse += np.sqrt(mean_squared_error(col_test, col_pred))
        avg_r2 += r2_score(col_test, col_pred)
    n = len(y_cols)
    print(f"[Regressor]  Avg MAE={avg_mae/n:.2f}  Avg RMSE={avg_rmse/n:.2f}  Avg R2={avg_r2/n:.2f}  -> Saved")

    # Save model
    model_path = os.path.join(models_dir, 'effect_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(reg, f)


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    train_effect_regressor(base_dir)
