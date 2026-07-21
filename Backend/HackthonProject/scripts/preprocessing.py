import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent


def get_dataset_paths():
    """Return the expected paths of all input datasets."""
    datasets_dir = BASE_DIR / "datasets"
    return {
        "news":      datasets_dir / "news_feed_dataset.csv",
        "shipping":  datasets_dir / "shipping_ais_dataset.csv",
        "sanctions": datasets_dir / "sanctions_dataset.csv",
        "oil":       datasets_dir / "oil_prices_dataset.csv",
    }


def load_datasets():
    """
    Load all 4 source datasets from the datasets directory.
    Raises FileNotFoundError if any dataset is missing or empty.
    """
    paths = get_dataset_paths()
    datasets = {}

    for name, path in paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing required dataset: {path.name} at {path.parent}")
        try:
            df = pd.read_csv(path)
            if df.empty:
                raise ValueError(f"Dataset {path.name} is empty.")
            datasets[name] = df
        except pd.errors.EmptyDataError:
            raise ValueError(f"Empty CSV file or invalid format: {path.name}")

    return datasets


def clean_data(datasets):
    """
    Perform date conversion, duplicate removal, and missing value handling
    on each dataset before merging.
    """
    cleaned = {}
    for name, df in datasets.items():
        df_copy = df.copy()

        if 'date' not in df_copy.columns:
            raise KeyError(f"Missing required 'date' column in dataset '{name}'.")

        try:
            df_copy['date'] = pd.to_datetime(df_copy['date']).dt.strftime('%Y-%m-%d')
        except Exception as e:
            raise ValueError(f"Date conversion failed for dataset '{name}': {str(e)}")

        df_copy = df_copy.drop_duplicates(subset=['date'])
        cleaned[name] = df_copy

    return cleaned


def normalize_features(df, numeric_cols):
    """Normalize specified continuous numeric columns using StandardScaler."""
    df_normalized = df.copy()
    if not numeric_cols:
        return df_normalized
    scaler = StandardScaler()
    df_normalized[numeric_cols] = scaler.fit_transform(df_normalized[numeric_cols])
    return df_normalized


def preprocess_all():
    """
    Run the end-to-end preprocessing workflow:
    Load → Clean → Merge → Fill Missing → Normalize.
    Returns the normalized merged DataFrame.
    """
    datasets = load_datasets()
    cleaned_datasets = clean_data(datasets)

    # Outer-join merge on 'date', sorted chronologically
    merged_df = cleaned_datasets['news']
    for name in ['shipping', 'sanctions', 'oil']:
        merged_df = pd.merge(merged_df, cleaned_datasets[name], on='date', how='outer')
    merged_df = merged_df.sort_values(by='date').reset_index(drop=True)

    numeric_cols = [
        'news_severity', 'tanker_movements', 'shipping_delays', 'vessel_congestion',
        'country_sanctions', 'supplier_sanctions', 'crude_price', 'daily_change', 'volatility'
    ]
    binary_cols = [
        'war_event', 'terrorism_event', 'cyber_attack_event', 'political_instability_event',
        'blocked_routes', 'export_restrictions', 'import_restrictions'
    ]

    merged_df[numeric_cols] = merged_df[numeric_cols].ffill().bfill()
    merged_df[binary_cols]  = merged_df[binary_cols].ffill().bfill()

    for col in numeric_cols:
        if col in merged_df.columns:
            median_val = merged_df[col].median()
            merged_df[col] = merged_df[col].fillna(0.0 if pd.isna(median_val) else median_val)

    for col in binary_cols:
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].fillna(0).astype(int)

    merged_df_normalized = normalize_features(merged_df, numeric_cols)

    # Keep raw (un-scaled) copies for feature engineering
    for col in numeric_cols:
        merged_df_normalized[f"{col}_raw"] = merged_df[col]

    return merged_df_normalized


if __name__ == "__main__":
    import sys
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.append(str(scripts_dir))

    from feature_engineering import run_feature_engineering
    from predict_risk import predict_risk
    from shap_explainer import explain_prediction
    from risk_reason_engine import generate_reasons, print_output_block

    preprocessed = preprocess_all()
    engineered   = run_feature_engineering(preprocessed)
    risk_class, risk_score = predict_risk()
    shap_df      = explain_prediction()
    reasons_df   = generate_reasons(shap_df, risk_class)
    print_output_block(risk_class, risk_score, reasons_df)
