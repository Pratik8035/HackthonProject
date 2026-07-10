import pandas as pd
import numpy as np
import pickle
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

BASE_DIR   = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)


def train_model():
    """
    Train a Random Forest Classifier on the engineered supply chain dataset,
    evaluate on a held-out test split, and save model artifacts to models/.

    Returns
    -------
    model         : trained RandomForestClassifier
    label_encoder : fitted LabelEncoder
    """
    dataset_path = BASE_DIR / "datasets" / "engineered_risk_dataset.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Engineered dataset not found at {dataset_path}. Run feature engineering first."
        )

    df = pd.read_csv(dataset_path)

    if len(df) < 10:
        raise ValueError(f"Insufficient records for training: {len(df)}")

    features_list = [
        'Conflict Score',
        'Shipping Delay Ratio',
        'Sanction Exposure',
        'Oil Price Change %',
        'Risk Frequency',
        'Historical Incident Count',
    ]

    for feat in features_list:
        if feat not in df.columns:
            raise KeyError(f"Required feature '{feat}' not found in engineered dataset.")

    if 'risk_level' not in df.columns:
        raise KeyError("Target column 'risk_level' not found in engineered dataset.")

    X = df[features_list]
    y = df['risk_level']

    label_encoder = LabelEncoder()
    label_encoder.fit(['LOW', 'MEDIUM', 'HIGH'])
    y_encoded = label_encoder.transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight='balanced',
        max_depth=6,
    )
    model.fit(X_train, y_train)

    y_pred    = model.predict(X_test)
    accuracy  = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall    = recall_score(y_test, y_pred, average='weighted')
    f1        = f1_score(y_test, y_pred, average='weighted')

    # Save artifacts
    with open(MODELS_DIR / "risk_model.pkl", 'wb') as f:
        pickle.dump(model, f)
    with open(MODELS_DIR / "label_encoder.pkl", 'wb') as f:
        pickle.dump(label_encoder, f)

    return model, label_encoder


if __name__ == "__main__":
    import sys
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.append(str(scripts_dir))

    from predict_risk import predict_risk
    from shap_explainer import explain_prediction
    from risk_reason_engine import generate_reasons, print_output_block

    train_model()
    risk_class, risk_score = predict_risk()
    shap_df    = explain_prediction()
    reasons_df = generate_reasons(shap_df, risk_class)
    print_output_block(risk_class, risk_score, reasons_df)
