import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def create_features(df):
    """
    Generate engineered features from the preprocessed dataframe:
    - Conflict Score
    - Shipping Delay Ratio
    - Sanction Exposure
    - Oil Price Change %
    - Risk Frequency
    - Historical Incident Count
    """
    df_feat = df.copy()

    # 1. Conflict Score: news severity weighted by event type
    df_feat['Conflict Score'] = df_feat['news_severity_raw'] * (
        df_feat['war_event']                    * 3.0 +
        df_feat['terrorism_event']              * 2.0 +
        df_feat['cyber_attack_event']           * 1.5 +
        df_feat['political_instability_event']  * 1.0 +
        1.0
    )

    # 2. Shipping Delay Ratio: delays relative to tanker movements
    df_feat['Shipping Delay Ratio'] = (
        df_feat['shipping_delays_raw'] / (df_feat['tanker_movements_raw'] + 1e-5)
    )

    # 3. Sanction Exposure: combined sanctions and restriction events
    df_feat['Sanction Exposure'] = (
        df_feat['country_sanctions_raw'] +
        df_feat['supplier_sanctions_raw'] +
        5.0 * df_feat['export_restrictions'] +
        5.0 * df_feat['import_restrictions']
    )

    # 4. Oil Price Change %: daily change relative to price
    df_feat['Oil Price Change %'] = (
        df_feat['daily_change_raw'] /
        (df_feat['crude_price_raw'] - df_feat['daily_change_raw'] + 1e-5)
    ) * 100.0

    # 5. Risk Frequency: 7-day rolling average of total incident count
    daily_incidents = (
        df_feat['war_event'] +
        df_feat['terrorism_event'] +
        df_feat['cyber_attack_event'] +
        df_feat['political_instability_event'] +
        df_feat['blocked_routes'] +
        df_feat['export_restrictions'] +
        df_feat['import_restrictions']
    )
    df_feat['Risk Frequency'] = daily_incidents.rolling(window=7, min_periods=1).mean()

    # 6. Historical Incident Count: cumulative sum of incidents
    df_feat['Historical Incident Count'] = daily_incidents.cumsum()

    return df_feat


def create_synthetic_target(df):
    """
    Calculate a synthetic target risk level (LOW / MEDIUM / HIGH)
    and risk_score (0–100) for model training.

    Thresholds are derived from the 33rd and 67th percentiles of the
    composite risk_index so that LOW / MEDIUM / HIGH are always
    equally represented in the training data regardless of the raw
    value distribution.
    """
    def scale_col(series):
        s_min, s_max = series.min(), series.max()
        if s_max - s_min < 1e-5:
            return pd.Series(0.0, index=series.index)
        return (series - s_min) / (s_max - s_min)

    s_conflict  = scale_col(df['Conflict Score'])
    s_delay     = scale_col(df['Shipping Delay Ratio'])
    s_sanctions = scale_col(df['Sanction Exposure'])
    s_oil_vol   = scale_col(df['volatility_raw'] if 'volatility_raw' in df.columns else df['volatility'])
    s_freq      = scale_col(df['Risk Frequency'])
    s_hist      = scale_col(df['Historical Incident Count'])

    avg_risk = (
        0.30 * s_conflict  +
        0.20 * s_delay     +
        0.15 * s_sanctions +
        0.15 * s_oil_vol   +
        0.10 * s_freq      +
        0.10 * s_hist
    )

    max_risk = np.maximum.reduce([s_conflict, s_delay, s_sanctions, s_oil_vol])

    # Combine average and maximum risk so that a single highly elevated indicator
    # (e.g. shipping delay or sanctions) can trigger MEDIUM or HIGH risk levels.
    risk_index = 0.4 * avg_risk + 0.6 * max_risk

    np.random.seed(42)
    noise       = np.random.normal(0, 0.05, len(df))
    final_index = np.clip(risk_index + noise, 0.0, 1.0)

    df['risk_score'] = np.round(final_index * 100.0).astype(int)

    # Use percentile-based thresholds so the training data always has
    # roughly equal numbers of LOW / MEDIUM / HIGH rows.
    low_thresh    = np.percentile(df['risk_score'], 33)
    medium_thresh = np.percentile(df['risk_score'], 67)

    df['risk_level'] = 'LOW'
    df.loc[df['risk_score'] >= low_thresh,    'risk_level'] = 'MEDIUM'
    df.loc[df['risk_score'] >= medium_thresh, 'risk_level'] = 'HIGH'

    # Re-scale the numeric score to sit inside the correct band (0-34 / 35-64 / 65-100)
    # so that predict_risk.py score computation stays consistent.
    low_mask    = df['risk_level'] == 'LOW'
    med_mask    = df['risk_level'] == 'MEDIUM'
    high_mask   = df['risk_level'] == 'HIGH'

    if low_mask.any():
        lo = df.loc[low_mask, 'risk_score']
        df.loc[low_mask, 'risk_score'] = (
            ((lo - lo.min()) / (lo.max() - lo.min() + 1e-9) * 34).round().astype(int)
        )
    if med_mask.any():
        me = df.loc[med_mask, 'risk_score']
        df.loc[med_mask, 'risk_score'] = (
            35 + ((me - me.min()) / (me.max() - me.min() + 1e-9) * 29).round().astype(int)
        )
    if high_mask.any():
        hi = df.loc[high_mask, 'risk_score']
        df.loc[high_mask, 'risk_score'] = (
            65 + ((hi - hi.min()) / (hi.max() - hi.min() + 1e-9) * 35).round().astype(int)
        )

    return df


def run_feature_engineering(preprocessed_df=None):
    """
    Run the feature engineering pipeline.
    Saves engineered_risk_dataset.csv to datasets/ and returns the DataFrame.
    """
    if preprocessed_df is None:
        from preprocessing import preprocess_all
        preprocessed_df = preprocess_all()

    df_features  = create_features(preprocessed_df)
    df_engineered = create_synthetic_target(df_features)

    output_path = BASE_DIR / "datasets" / "engineered_risk_dataset.csv"
    df_engineered.to_csv(output_path, index=False)

    return df_engineered


if __name__ == "__main__":
    import sys
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.append(str(scripts_dir))

    from predict_risk import predict_risk
    from shap_explainer import explain_prediction
    from risk_reason_engine import generate_reasons, print_output_block

    engineered             = run_feature_engineering()
    risk_class, risk_score = predict_risk()
    shap_df                = explain_prediction()
    reasons_df             = generate_reasons(shap_df, risk_class)
    print_output_block(risk_class, risk_score, reasons_df)
