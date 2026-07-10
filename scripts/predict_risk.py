import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime

BASE_DIR   = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


def predict_risk(latest_observation=None):
    """
    Load the trained Random Forest model and predict risk class and score
    for the latest observation in engineered_risk_dataset.csv.

    Returns
    -------
    risk_class : str   — 'LOW', 'MEDIUM', or 'HIGH'
    risk_score : int   — 0–100
    """
    model_path = MODELS_DIR / "risk_model.pkl"
    le_path    = MODELS_DIR / "label_encoder.pkl"

    if not model_path.exists() or not le_path.exists():
        raise FileNotFoundError(
            "Trained model or label encoder not found in models/. Run train_model.py first."
        )

    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(le_path, 'rb') as f:
        label_encoder = pickle.load(f)

    features_list = [
        'Conflict Score',
        'Shipping Delay Ratio',
        'Sanction Exposure',
        'Oil Price Change %',
        'Risk Frequency',
        'Historical Incident Count',
    ]

    if latest_observation is None:
        dataset_path = BASE_DIR / "datasets" / "engineered_risk_dataset.csv"
        if not dataset_path.exists():
            raise FileNotFoundError(
                f"Engineered dataset not found at {dataset_path}. Run feature engineering first."
            )
        df = pd.read_csv(dataset_path)
        if df.empty:
            raise ValueError("Engineered dataset is empty.")
        latest_observation = df.iloc[-1][features_list].to_frame().T
    else:
        if isinstance(latest_observation, pd.Series):
            latest_observation = latest_observation.to_frame().T
        elif isinstance(latest_observation, dict):
            latest_observation = pd.DataFrame([latest_observation])
        for feat in features_list:
            if feat not in latest_observation.columns:
                raise KeyError(f"Input observation missing feature '{feat}'")
        latest_observation = latest_observation[features_list]

    prediction = model.predict(latest_observation)[0]
    prob       = model.predict_proba(latest_observation)[0]
    risk_class = label_encoder.inverse_transform([prediction])[0]

    classes    = list(label_encoder.classes_)
    low_idx    = classes.index('LOW')
    medium_idx = classes.index('MEDIUM')
    high_idx   = classes.index('HIGH')

    # Map the classifier's class probabilities to the full set of label encoder indices
    full_probs = np.zeros(len(classes))
    for i, cls_val in enumerate(model.classes_):
        full_probs[cls_val] = prob[i]

    if risk_class == 'LOW':
        base_score = 10
        extra      = int(round(full_probs[medium_idx] * 15 + full_probs[high_idx] * 20))
        risk_score = min(34, base_score + extra)
    elif risk_class == 'MEDIUM':
        base_score = 35
        diff       = full_probs[high_idx] - full_probs[low_idx]
        extra      = int(round((diff + 1) / 2.0 * 29))
        risk_score = min(64, base_score + extra)
    else:  # HIGH
        base_score = 65
        extra      = int(round((full_probs[high_idx] + full_probs[medium_idx] * 0.2) * 35))
        risk_score = min(100, base_score + extra)

    return risk_class, risk_score


if __name__ == "__main__":
    import sys
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.append(str(scripts_dir))

    from shap_explainer import explain_prediction
    from risk_reason_engine import generate_reasons, print_output_block

    risk_class, risk_score = predict_risk()
    shap_df    = explain_prediction()
    reasons_df = generate_reasons(shap_df, risk_class)
    print_output_block(risk_class, risk_score, reasons_df)
