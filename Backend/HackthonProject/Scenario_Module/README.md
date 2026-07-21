# Scenario Simulation & Effects Calculation Module

This module implements a supply-chain disruption simulator using a RandomForestClassifier to identify disruption scenarios and a RandomForestRegressor to calculate the business effects of those disruptions.

## Project Structure
- `datasets/`: Contains 9 raw CSV datasets (200 rows each)
- `models/`: Saved models, encoders, and scalers
- `outputs/`: Prediction outputs (`scenario_simulation_output.csv`, `effect_calculation_output.csv`)
- `scripts/`: Implementation scripts
  - `generate_mock_data.py`: Generates the synthetic datasets
  - `preprocessing.py`: Implements label encoding and data preprocessing
  - `feature_engineering.py`: Implements key features and normalization (StandardScaler)
  - `train_scenario_model.py`: Trains and evaluates the RandomForestClassifier
  - `train_effect_model.py`: Trains and evaluates the RandomForestRegressor
  - `scenario_prediction.py`: Performs scenario inference and top 4 ranking
  - `effect_prediction.py`: Computes the downstream impacts and overall risk score
  - `shap_explainer.py`: (Optional) Performs SHAP explainability analysis
  - `run_module.py`: Linear pipeline execution script orchestrating everything

## Running the module
Ensure python dependencies are installed:
```bash
pip install -r requirements.txt
```
To run the full end-to-end pipeline and interactive prompt:
```bash
python scripts/run_module.py
```
