import pandas as pd
import numpy as np
import pickle
import shap
from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


def explain_prediction(latest_observation=None):
    """
    Use SHAP TreeExplainer to explain the risk prediction for the latest
    observation.

    Returns
    -------
    shap_df : pd.DataFrame
        Columns: Feature, SHAP Value, Absolute Importance — sorted descending.
    """
    model_path = MODELS_DIR / "risk_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError("Model not found. Run train_model.py first.")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

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
            raise FileNotFoundError(f"Engineered dataset not found at {dataset_path}.")
        df = pd.read_csv(dataset_path)
        if df.empty:
            raise ValueError("Engineered dataset is empty.")
        latest_observation = df.iloc[-1][features_list].to_frame().T
    else:
        if isinstance(latest_observation, pd.Series):
            latest_observation = latest_observation.to_frame().T
        elif isinstance(latest_observation, dict):
            latest_observation = pd.DataFrame([latest_observation])
        latest_observation = latest_observation[features_list]

    explainer        = shap.TreeExplainer(model)
    raw_shap_output  = explainer.shap_values(latest_observation)
    pred_class_label = model.predict(latest_observation)[0]

    # Map the predicted class label to its index in model.classes_ to align with SHAP outputs
    if hasattr(model, "classes_") and pred_class_label in model.classes_:
        pred_class_idx = list(model.classes_).index(pred_class_label)
    else:
        pred_class_idx = 0

    if isinstance(raw_shap_output, list):
        feat_shaps = raw_shap_output[pred_class_idx][0]
    elif isinstance(raw_shap_output, np.ndarray):
        if raw_shap_output.ndim == 3:
            feat_shaps = raw_shap_output[0, :, pred_class_idx]
        elif raw_shap_output.ndim == 2:
            feat_shaps = raw_shap_output[0]
        else:
            feat_shaps = raw_shap_output.flatten()
    elif hasattr(raw_shap_output, "values"):
        vals = raw_shap_output.values
        feat_shaps = vals[0, :, pred_class_idx] if vals.ndim == 3 else vals[0]
    else:
        feat_shaps = np.array(raw_shap_output).flatten()

    shap_df = pd.DataFrame({
        "Feature":             latest_observation.columns.tolist(),
        "SHAP Value":          feat_shaps,
        "Absolute Importance": np.abs(feat_shaps),
    }).sort_values("Absolute Importance", ascending=False).reset_index(drop=True)

    return shap_df


if __name__ == "__main__":
    import sys
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.append(str(scripts_dir))

    from predict_risk import predict_risk
    from risk_reason_engine import generate_reasons, print_output_block

    risk_class, risk_score = predict_risk()
    shap_df    = explain_prediction()
    reasons_df = generate_reasons(shap_df, risk_class)
    print_output_block(risk_class, risk_score, reasons_df)
