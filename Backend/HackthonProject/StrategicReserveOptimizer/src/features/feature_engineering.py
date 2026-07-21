"""
Strategic Reserve Optimization Agent
Feature Engineering Module

Generates all ML and optimization features from the master dataset.
Features include: lag variables, rolling statistics, composite risk indices,
seasonality decomposition, and optimization-specific features.

Author: Strategic Reserve Optimization Team
Date: 2025
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import pickle

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def add_lag_features(df: pd.DataFrame, cols: list, lags: list = [1, 3, 6, 12]) -> pd.DataFrame:
    """Add lag features for key time series columns."""
    for col in cols:
        if col not in df.columns:
            continue
        for lag in lags:
            df[f"{col}_lag{lag}"] = df[col].shift(lag)
    return df


def add_rolling_features(df: pd.DataFrame, cols: list,
                         windows: list = [3, 6, 12]) -> pd.DataFrame:
    """Add rolling mean, std, and min/max features."""
    for col in cols:
        if col not in df.columns:
            continue
        for w in windows:
            df[f"{col}_roll{w}m_mean"] = df[col].rolling(window=w, min_periods=1).mean()
            df[f"{col}_roll{w}m_std"] = df[col].rolling(window=w, min_periods=1).std().fillna(0)
            if w >= 6:
                df[f"{col}_roll{w}m_min"] = df[col].rolling(window=w, min_periods=1).min()
                df[f"{col}_roll{w}m_max"] = df[col].rolling(window=w, min_periods=1).max()
    return df


def add_trend_features(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Add momentum/trend features (rate of change)."""
    for col in cols:
        if col not in df.columns:
            continue
        df[f"{col}_mom1m"] = df[col].pct_change(1).fillna(0)
        df[f"{col}_mom3m"] = df[col].pct_change(3).fillna(0)
        df[f"{col}_mom6m"] = df[col].pct_change(6).fillna(0)
    return df


def add_seasonality_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add Fourier-based seasonality features."""
    if "date" not in df.columns:
        return df
    
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["year"] = df["date"].dt.year
    df["year_normalized"] = (df["year"] - df["year"].min()) / max(1, df["year"].max() - df["year"].min())
    
    # Fourier terms for annual seasonality
    df["sin_annual"] = np.sin(2 * np.pi * df["month"] / 12)
    df["cos_annual"] = np.cos(2 * np.pi * df["month"] / 12)
    df["sin_semi"] = np.sin(4 * np.pi * df["month"] / 12)
    df["cos_semi"] = np.cos(4 * np.pi * df["month"] / 12)
    
    # Quarter dummies
    for q in [1, 2, 3, 4]:
        df[f"q{q}"] = (df["quarter"] == q).astype(int)
    
    # Winter/Summer demand peaks
    df["is_winter"] = df["month"].isin([11, 12, 1, 2]).astype(int)
    df["is_monsoon"] = df["month"].isin([6, 7, 8, 9]).astype(int)
    
    return df


def compute_geopolitical_risk_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a composite Geopolitical Risk Index (GRI).
    Weights: war/conflict 40%, Hormuz risk 30%, sanctions 20%, shipping 10%
    """
    if all(c in df.columns for c in ["geopolitical_severity", "hormuz_closure_risk",
                                      "india_sanctions_exposure_score", "redsea_disruption_risk"]):
        df["composite_gri"] = (
            0.35 * df["geopolitical_severity"] / 10.0 +
            0.30 * df["hormuz_closure_risk"] +
            0.20 * df["india_sanctions_exposure_score"] / 10.0 +
            0.15 * df["redsea_disruption_risk"]
        ).round(4)
    return df


def compute_supply_stress_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Supply Stress Index (SSI): composite indicator of supply vulnerability.
    Incorporates: HHI concentration, GRI, shipping delays, SPR coverage.
    """
    if "hhi_concentration" in df.columns:
        hhi_norm = df["hhi_concentration"] / df["hhi_concentration"].max()
    else:
        hhi_norm = 0.0
    
    if "coverage_days" in df.columns:
        # Lower coverage = higher stress (inverted, normalized to 0-1)
        spr_stress = (1 - df["coverage_days"].clip(0, 180) / 180).fillna(0.5)
    else:
        spr_stress = 0.5
    
    if "composite_gri" in df.columns:
        gri = df["composite_gri"]
    else:
        gri = 0.3
    
    if "hormuz_extra_delay_days" in df.columns:
        delay_stress = (df["hormuz_extra_delay_days"] / 
                        df["hormuz_extra_delay_days"].clip(lower=0.01).max()).fillna(0)
    else:
        delay_stress = 0.0
    
    df["supply_stress_index"] = (
        0.30 * hhi_norm +
        0.30 * spr_stress +
        0.25 * gri +
        0.15 * delay_stress
    ).round(4)
    
    return df


def compute_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute price-derived features."""
    if "india_basket_usd" not in df.columns:
        return df
    
    # Price momentum
    df["price_mom_1m"] = df["india_basket_usd"].pct_change(1).fillna(0)
    df["price_mom_3m"] = df["india_basket_usd"].pct_change(3).fillna(0)
    df["price_mom_12m"] = df["india_basket_usd"].pct_change(12).fillna(0)
    
    # Price volatility (20-period rolling std normalized)
    df["price_volatility_6m"] = df["india_basket_usd"].rolling(6, min_periods=1).std().fillna(0)
    df["price_volatility_12m"] = df["india_basket_usd"].rolling(12, min_periods=1).std().fillna(0)
    
    # Spread: Brent vs India basket
    if "brent_usd" in df.columns:
        df["brent_india_spread"] = (df["brent_usd"] - df["india_basket_usd"]).round(3)
    
    # Import cost estimate (USD/month)
    if "total_imports_mmt" in df.columns and "usdinr" in df.columns:
        # 1 MMT crude ≈ 7.33 million barrels
        df["monthly_import_cost_bn_usd"] = (
            df["total_imports_mmt"] * 7.33 * df["india_basket_usd"] / 1000
        ).round(3)
    
    return df


def compute_spr_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute SPR-specific optimization features."""
    if "total_spr_stock_mmt" not in df.columns:
        return df
    
    # SPR fill rate (change per month)
    df["spr_fill_rate_mmt"] = df["total_spr_stock_mmt"].diff().fillna(0)
    
    # Days of consumption coverage
    if "total_consumption_mmt" in df.columns:
        df["spr_consumption_days"] = (
            df["total_spr_stock_mmt"] / (df["total_consumption_mmt"] / 30)
        ).round(1)
    
    # SPR deficit from IEA 90-day target
    if "coverage_days" in df.columns:
        df["spr_deficit_days"] = (90 - df["coverage_days"]).clip(lower=0).round(1)
        df["spr_surplus_days"] = (df["coverage_days"] - 90).clip(lower=0).round(1)
    
    # Rolling SPR trend
    df["spr_trend_3m"] = df["total_spr_stock_mmt"].rolling(3, min_periods=1).mean()
    df["spr_trend_6m"] = df["total_spr_stock_mmt"].rolling(6, min_periods=1).mean()
    
    return df


def compute_import_diversification(df: pd.DataFrame) -> pd.DataFrame:
    """Compute import source diversification metrics."""
    supplier_cols = ["iraq_mmt", "saudi_arabia_mmt", "russia_mmt",
                     "uae_mmt", "kuwait_mmt", "nigeria_mmt", "usa_mmt", "iran_mmt"]
    
    available_cols = [c for c in supplier_cols if c in df.columns]
    if not available_cols or "total_imports_mmt" not in df.columns:
        return df
    
    total = df["total_imports_mmt"].replace(0, np.nan)
    
    # Share of each supplier
    for col in available_cols:
        supplier = col.replace("_mmt", "")
        df[f"{supplier}_share_pct"] = (df[col] / total * 100).fillna(0).round(2)
    
    # Maximum supplier concentration
    share_cols = [f"{c.replace('_mmt','')}_share_pct" for c in available_cols]
    df["max_supplier_concentration"] = df[share_cols].max(axis=1)
    
    # Number of active suppliers (>5% share)
    df["n_active_suppliers"] = (df[share_cols] > 5).sum(axis=1)
    
    # Russia dependency (strategic risk metric)
    if "russia_mmt" in df.columns:
        df["russia_dependency_pct"] = (df["russia_mmt"] / total * 100).fillna(0).round(2)
    
    # OPEC dependency
    opec_cols = [c for c in ["iraq_mmt", "saudi_arabia_mmt", "uae_mmt",
                              "kuwait_mmt", "nigeria_mmt", "iran_mmt"] if c in df.columns]
    df["opec_dependency_pct"] = (df[opec_cols].sum(axis=1) / total * 100).fillna(0).round(2)
    
    return df


def compute_shipping_risk_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute composite shipping risk features."""
    if "hormuz_extra_delay_days" not in df.columns:
        return df
    
    # Combined route risk score
    hormuz_risk = df.get("hormuz_closure_risk", pd.Series(0.1, index=df.index))
    redsea_risk = df.get("redsea_disruption_risk", pd.Series(0.1, index=df.index))
    
    df["combined_route_risk"] = (0.6 * hormuz_risk + 0.4 * redsea_risk).round(4)
    
    # Shipping cost impact on import cost
    if "shipping_cost_premium_usd_bbl" in df.columns and "total_imports_mmt" in df.columns:
        df["monthly_shipping_premium_mn_usd"] = (
            df["shipping_cost_premium_usd_bbl"] * df["total_imports_mmt"] * 7.33
        ).round(2)
    
    # Total effective transit time
    if "hormuz_transit_days" in df.columns and "redsea_extra_delay_days" in df.columns:
        df["effective_transit_days_gulf"] = (
            df["hormuz_transit_days"] + df["redsea_extra_delay_days"] * 0.3
        ).round(1)
    
    return df


def add_target_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create target variables for each forecasting task.
    
    Targets:
    1. price_next_month: Next month's India basket price (regression)
    2. demand_next_month: Next month's total consumption (regression)
    3. supply_disruption: Binary flag if supply falls >10% vs prior month (classification)
    4. shipping_delay_increase: Binary if shipping delay increases >2 days (classification)
    """
    if "india_basket_usd" in df.columns:
        df["price_target_next_month"] = df["india_basket_usd"].shift(-1)
        df["price_target_3m_avg"] = df["india_basket_usd"].shift(-1).rolling(3).mean().shift(-2)
    
    if "total_consumption_mmt" in df.columns:
        df["demand_target_next_month"] = df["total_consumption_mmt"].shift(-1)
    
    if "total_imports_mmt" in df.columns:
        import_change = df["total_imports_mmt"].pct_change(-1)
        df["supply_disruption_target"] = (import_change < -0.10).astype(float).shift(1).fillna(0)
    
    if "hormuz_extra_delay_days" in df.columns:
        delay_increase = df["hormuz_extra_delay_days"].diff(-1)
        df["shipping_delay_target"] = (delay_increase > 2.0).astype(float).shift(1).fillna(0)
    
    return df


def run_feature_engineering() -> pd.DataFrame:
    """
    Full feature engineering pipeline.
    Loads master dataset → engineers features → saves feature-rich dataset.
    """
    logger.info("=" * 70)
    logger.info("Starting Feature Engineering Pipeline")
    logger.info("=" * 70)
    
    master_path = PROCESSED_DIR / "master_dataset.csv"
    if not master_path.exists():
        raise FileNotFoundError(
            f"Master dataset not found at {master_path}. Run preprocessor.py first."
        )
    
    df = pd.read_csv(master_path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    logger.info(f"Loaded master dataset: {df.shape}")
    
    # -- 1. Seasonality features --------------------------------------------
    logger.info("Adding seasonality features...")
    df = add_seasonality_features(df)
    
    # -- 2. Lag features ---------------------------------------------------
    logger.info("Adding lag features...")
    lag_cols = ["india_basket_usd", "total_imports_mmt", "total_consumption_mmt",
                "total_spr_stock_mmt", "opec_total_mmbd", "geopolitical_risk_index",
                "hhi_concentration", "vlcc_freight_rate_usd_day"]
    df = add_lag_features(df, lag_cols, lags=[1, 3, 6, 12])
    
    # -- 3. Rolling features -----------------------------------------------
    logger.info("Adding rolling statistics...")
    roll_cols = ["india_basket_usd", "total_imports_mmt", "total_consumption_mmt",
                 "geopolitical_severity", "hormuz_closure_risk"]
    df = add_rolling_features(df, roll_cols, windows=[3, 6, 12])
    
    # -- 4. Trend / momentum -----------------------------------------------
    logger.info("Adding trend features...")
    trend_cols = ["india_basket_usd", "total_imports_mmt", "opec_total_mmbd"]
    df = add_trend_features(df, trend_cols)
    
    # -- 5. Price features -------------------------------------------------
    logger.info("Computing price features...")
    df = compute_price_features(df)
    
    # -- 6. SPR features ---------------------------------------------------
    logger.info("Computing SPR features...")
    df = compute_spr_features(df)
    
    # -- 7. Geopolitical risk index ----------------------------------------
    logger.info("Computing Geopolitical Risk Index...")
    df = compute_geopolitical_risk_index(df)
    
    # -- 8. Supply stress index --------------------------------------------
    logger.info("Computing Supply Stress Index...")
    df = compute_supply_stress_index(df)
    
    # -- 9. Import diversification -----------------------------------------
    logger.info("Computing import diversification metrics...")
    df = compute_import_diversification(df)
    
    # -- 10. Shipping risk -------------------------------------------------
    logger.info("Computing shipping risk features...")
    df = compute_shipping_risk_features(df)
    
    # -- 11. Target variables ----------------------------------------------
    logger.info("Adding target variables...")
    df = add_target_variables(df)
    
    # -- 12. Clean up NaNs from lags ---------------------------------------
    # Drop rows with NaN in critical columns (first 12 rows due to lags)
    critical_lag_cols = [c for c in df.columns if "_lag12" in c]
    if critical_lag_cols:
        df = df.dropna(subset=critical_lag_cols[:3]).reset_index(drop=True)
    
    # Fill any remaining NaNs
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    
    # -- 13. Save feature-rich dataset -------------------------------------
    out_path = PROCESSED_DIR / "features_dataset.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"\nOK Feature dataset saved: {out_path}")
    logger.info(f"  Shape: {df.shape}")
    logger.info(f"  Features: {len(df.columns)} columns")
    
    # Save feature scaler
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                    if not c.startswith("price_target") and not c.startswith("demand_target")
                    and not c.endswith("_target") and c not in ["month", "quarter", "year"]]
    
    scaler = StandardScaler()
    scaler.fit(df[feature_cols].fillna(0))
    
    scaler_path = MODELS_DIR / "feature_scaler.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump({"scaler": scaler, "feature_cols": feature_cols}, f)
    
    logger.info(f"  Scaler saved: {scaler_path}")
    
    return df


if __name__ == "__main__":
    run_feature_engineering()
