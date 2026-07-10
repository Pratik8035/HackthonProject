# Risk Intelligence Module

The **Risk Intelligence Module** is a backend-only AI/ML supply chain risk prediction system designed for Energy Supply Chain Resilience. It processes multiple external risk factor streams, engineers features, trains a Random Forest Classifier to identify risk levels, utilizes SHAP (SHapley Additive exPlanations) for model explainability, and uses a rules-based natural language engine to convert feature importance and values into readable reasons.

## Project Structure

```text
Risk_Intelligence_Module/
├── datasets/                           # Input and engineered CSV files
│   ├── news_feed_dataset.csv           # Geopolitical alerts & event severity
│   ├── shipping_ais_dataset.csv        # Tanker movements, congestion, route blocks
│   ├── sanctions_dataset.csv           # Blocked countries/suppliers & export restrictions
│   ├── oil_prices_dataset.csv          # Crude oil pricing, changes, and volatility
│   └── engineered_risk_dataset.csv     # Combined dataset generated during feature engineering
├── models/                             # Serialized ML artifacts
│   ├── risk_model.pkl                  # Trained Random Forest model binary
│   ├── label_encoder.pkl               # Saved Label Encoder state
│   └── model_metadata.json             # JSON file documenting training details & metrics
├── scripts/                            # Core python scripts
│   ├── generate_mock_data.py           # Developer utility to populate datasets/
│   ├── preprocessing.py                # Loads, cleans, merges, and normalizes datasets
│   ├── feature_engineering.py          # Calculates features and synthetic targets
│   ├── train_model.py                  # Trains and serializes the classifier
│   ├── predict_risk.py                 # Predicts risk for the latest data point
│   ├── shap_explainer.py               # Generates feature importances using SHAP
│   ├── risk_reason_engine.py           # Translates SHAP values to readable explanations
│   └── run_module.py                   # End-to-end master orchestrator
└── requirements.txt                    # Python library requirements
```

## Input Dataset Formats

All datasets must reside in the `datasets/` folder and contain a `date` column formatted as `YYYY-MM-DD`.

1. **`news_feed_dataset.csv`**: Contains geopolitical events.
   - `date`, `war_event` (0 or 1), `terrorism_event` (0 or 1), `cyber_attack_event` (0 or 1), `political_instability_event` (0 or 1), `news_severity` (0 to 10 float).
2. **`shipping_ais_dataset.csv`**: Contains logistics and transit statuses.
   - `date`, `tanker_movements` (integer), `shipping_delays` (integer), `blocked_routes` (0 or 1), `vessel_congestion` (0 to 10 float).
3. **`sanctions_dataset.csv`**: Contains regulatory and export blocks.
   - `date`, `country_sanctions` (integer), `supplier_sanctions` (integer), `export_restrictions` (0 or 1), `import_restrictions` (0 or 1).
4. **`oil_prices_dataset.csv`**: Contains energy commodity pricing.
   - `date`, `crude_price` (float), `daily_change` (float), `volatility` (float).

## Installation

To install dependencies, run:

```bash
pip install -r requirements.txt
```

## Usage and Commands

Execute commands from the root directory of the project:

### 1. Training

Trains the Random Forest model and saves it to `models/`:

```bash
python scripts/train_model.py
```

### 2. Prediction

Predicts the overall supply chain risk for the latest row of data:

```bash
python scripts/predict_risk.py
```

### 3. SHAP Explainability

Calculates SHAP values for the prediction:

```bash
python scripts/shap_explainer.py
```

### 4. Risk Reasons

Generates dynamic human-readable reasons for the predicted risk:

```bash
python scripts/risk_reason_engine.py
```

### 5. Run Complete Module

Orchestrates the entire sequence (Preprocessing, Feature Engineering, Conditional Training, Inference, SHAP explainability, and Reason generation) in one command:

```bash
python scripts/run_module.py
```

## Logging and Error Handling

- **Logs**: Execution metadata, model evaluations, status, warning, and error tracks are appended to `logs/risk_module.log`.
- **Validation**: Scripts validate that datasets exist before loading. If any file is missing, empty, or corrupted, the program will write to the logs and print a descriptive error to the console instead of generating mock datasets or crashing silently.
