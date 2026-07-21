"""
Strategic Reserve Optimization Agent
Daily Preprocessor & Feature Engineering

Merges daily datasets and creates rolling window features for ML models.
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROC_DATA_DIR = BASE_DIR / "data" / "processed"
PROC_DATA_DIR.mkdir(parents=True, exist_ok=True)

def merge_and_preprocess():
    """Merge all raw daily files into a single master dataframe."""
    logger.info("Merging daily datasets...")
    
    files = ["daily_prices.csv", "daily_refinery_demand.csv", 
             "daily_supplier_availability.csv", "daily_spr_inventory.csv",
             "daily_geopolitics.csv"]
             
    master_df = None
    for f in files:
        path = RAW_DATA_DIR / f
        if not path.exists():
            logger.warning(f"File not found: {path}")
            continue
            
        df = pd.read_csv(path, parse_dates=["date"])
        if master_df is None:
            master_df = df
        else:
            master_df = pd.merge(master_df, df, on="date", how="inner")
            
    # Forward fill any missing daily data
    master_df = master_df.sort_values("date").fillna(method="ffill").fillna(0)
    return master_df

def engineer_features(df):
    """Create lag and rolling features for daily operational prediction."""
    logger.info("Engineering daily features...")
    
    df = df.sort_values("date").copy()
    
    # 1. Temporal Features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    
    # 2. Rolling Statistics (7, 14, 30 days)
    target_cols = ["crude_price_usd", "total_demand_kmt", "total_avail_kmt", "geopolitical_risk_score"]
    windows = [7, 14, 30]
    
    for col in target_cols:
        for w in windows:
            df[f"{col}_roll_{w}d_mean"] = df[col].rolling(w, min_periods=1).mean()
            df[f"{col}_roll_{w}d_std"] = df[col].rolling(w, min_periods=1).std().fillna(0)
            
        # Lags
        for lag in [1, 2, 3, 7]:
            df[f"{col}_lag_{lag}"] = df[col].shift(lag).fillna(method="bfill")
            
    # 3. Supply-Demand Balance Indicator
    df["daily_deficit_kmt"] = df["total_demand_kmt"] - df["total_avail_kmt"]
    df["deficit_roll_7d"] = df["daily_deficit_kmt"].rolling(7, min_periods=1).mean()
    
    # 4. Target Variables (Predicting next day's price and deficit)
    df["target_price_next_day"] = df["crude_price_usd"].shift(-1)
    df["target_deficit_next_day"] = df["daily_deficit_kmt"].shift(-1)
    
    # Drop rows with NaN targets (last row)
    df = df.dropna(subset=["target_price_next_day"])
    
    path = PROC_DATA_DIR / "daily_features.csv"
    df.to_csv(path, index=False)
    logger.info(f"Saved processed features -> {path} (shape: {df.shape})")
    
    return True

if __name__ == "__main__":
    master = merge_and_preprocess()
    engineer_features(master)
