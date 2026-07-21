"""
Strategic Reserve Optimization Agent
Daily Machine Learning Forecasting Models

Trains models to predict short-term crude prices and supply deficits.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import pickle
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb
import lightgbm as lgb

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROC_DATA_DIR = BASE_DIR / "data" / "processed"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def train_models():
    """Train XGBoost for price and LightGBM for supply deficit."""
    features_path = PROC_DATA_DIR / "daily_features.csv"
    if not features_path.exists():
        logger.error(f"Features file missing at {features_path}")
        return False
        
    df = pd.read_csv(features_path)
    
    # Exclude non-feature columns
    drop_cols = ["date", "target_price_next_day", "target_deficit_next_day"]
    features = [c for c in df.columns if c not in drop_cols]
    
    X = df[features]
    y_price = df["target_price_next_day"]
    y_deficit = df["target_deficit_next_day"]
    
    # Train/Test Split (Time Series: 80/20)
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_price_train, y_price_test = y_price.iloc[:split_idx], y_price.iloc[split_idx:]
    y_def_train, y_def_test = y_deficit.iloc[:split_idx], y_deficit.iloc[split_idx:]
    
    logger.info("Training XGBoost for Daily Price Forecasting...")
    xgb_model = xgb.XGBRegressor(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42)
    xgb_model.fit(X_train, y_price_train)
    
    p_preds = xgb_model.predict(X_test)
    mae_p = mean_absolute_error(y_price_test, p_preds)
    r2_p = r2_score(y_price_test, p_preds)
    logger.info(f"Price Model - MAE: {mae_p:.2f} USD, R2: {r2_p:.4f}")
    
    with open(MODEL_DIR / "xgb_daily_price.pkl", "wb") as f:
        pickle.dump(xgb_model, f)
        
    logger.info("Training LightGBM for Daily Deficit Forecasting...")
    lgb_model = lgb.LGBMRegressor(n_estimators=150, num_leaves=31, learning_rate=0.05, random_state=42)
    lgb_model.fit(X_train, y_def_train)
    
    d_preds = lgb_model.predict(X_test)
    mae_d = mean_absolute_error(y_def_test, d_preds)
    r2_d = r2_score(y_def_test, d_preds)
    logger.info(f"Deficit Model - MAE: {mae_d:.2f} kMT, R2: {r2_d:.4f}")
    
    with open(MODEL_DIR / "lgb_daily_deficit.pkl", "wb") as f:
        pickle.dump(lgb_model, f)
        
    # Save the feature list
    with open(MODEL_DIR / "feature_list.pkl", "wb") as f:
        pickle.dump(features, f)
        
    logger.info("Daily ML Training Complete.")
    return True

if __name__ == "__main__":
    train_models()
