import os
import sys

# Ensure scripts folder is on the Python path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(scripts_dir)

from generate_mock_data import generate_all_mock_data
from train_scenario_model import train_scenario_classifier
from train_effect_model import train_effect_regressor
from scenario_prediction import run_scenario_prediction
from effect_prediction import run_effect_prediction

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1. Generate datasets
    try:
        datasets_dir = os.path.join(base_dir, 'datasets')
        generate_all_mock_data(datasets_dir)
    except Exception as e:
        print(f"FATAL ERROR during dataset generation: {e}")
        sys.exit(1)

    # 2. Train and Evaluate Scenario Simulation Model
    try:
        train_scenario_classifier(base_dir)
    except Exception as e:
        print(f"FATAL ERROR during scenario model training: {e}")
        sys.exit(1)

    # 3. Train and Evaluate Effects Calculation Model
    try:
        train_effect_regressor(base_dir)
        print("Pipeline ready.")
    except Exception as e:
        print(f"FATAL ERROR during effects model training: {e}")
        sys.exit(1)

    # 4. Perform Scenario Simulation & User Prompt
    try:
        scenario_id, scenario_name, scenario_prob = run_scenario_prediction(base_dir)
    except Exception as e:
        print(f"FATAL ERROR during scenario simulation: {e}")
        sys.exit(1)

    # 5. Perform Effects Calculation on Selected Scenario
    try:
        run_effect_prediction(base_dir, scenario_id, scenario_name, scenario_prob)
        print("Pipeline execution completed successfully.")
    except Exception as e:
        print(f"FATAL ERROR during effects calculation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
