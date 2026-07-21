import sys
from pathlib import Path
from datetime import datetime

# Add scripts directory to path for sibling imports
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

BASE_DIR   = SCRIPTS_DIR.parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

from preprocessing      import preprocess_all
from feature_engineering import run_feature_engineering
from train_model         import train_model
from predict_risk        import predict_risk
from shap_explainer      import explain_prediction
from risk_reason_engine  import generate_reasons, print_output_block
from scenario_generator  import generate_scenario


def main():
    """
    End-to-end pipeline — fully in-memory, no outputs/ or logs/ folders.

    Steps:
      1. Apply scenario  (mutates last row of source CSVs)
      2. Preprocess      (merge + normalise → DataFrame)
      3. Feature engineer (compute features + labels → save engineered CSV)
      4. Train if needed  (model artefacts → models/)
      5. Predict          (risk class + score)
      6. SHAP explain     (feature importances)
      7. Reason engine    (human-readable drivers)
      8. Print result
    """
    start = datetime.now()

    try:
        # 1. Scenario
        scenario_name  = generate_scenario()

        # 2. Preprocess
        preprocessed   = preprocess_all()

        # 3. Feature engineering
        run_feature_engineering(preprocessed)

        # 4. Train if model artefacts are missing
        if not (MODELS_DIR / "risk_model.pkl").exists() or \
           not (MODELS_DIR / "label_encoder.pkl").exists():
            train_model()

        # 5. Predict
        risk_class, risk_score = predict_risk()

        # 6. SHAP
        shap_df    = explain_prediction()

        # 7. Reasons
        reasons_df = generate_reasons(shap_df, risk_class)

        # 8. Output
        print_output_block(risk_class, risk_score, reasons_df)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
