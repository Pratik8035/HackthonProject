import os
import pickle
import pandas as pd
import numpy as np
from colorama import init, Fore, Style
init(autoreset=True)
from preprocessing import load_all_datasets, preprocess_categorical
from feature_engineering import engineer_features, scale_features

def run_scenario_prediction(base_dir):
    data_dir = os.path.join(base_dir, 'datasets')
    models_dir = os.path.join(base_dir, 'models')
    
    # 1. Load trained model, scaler, and encoders
    with open(os.path.join(models_dir, 'scenario_model.pkl'), 'rb') as f:
        clf = pickle.load(f)
    with open(os.path.join(models_dir, 'scenario_scaler.pkl'), 'rb') as f:
        scaler = pickle.load(f)
    with open(os.path.join(models_dir, 'scenario_encoder.pkl'), 'rb') as f:
        encoders = pickle.load(f)
        
    # 2. Load and engineer features of all current master scenarios
    datasets = load_all_datasets(data_dir)
    df = engineer_features(datasets)
    
    # Encode and scale
    categorical_cols = ['Scenario Type', 'Severity', 'Affected Region', 'Affected Commodity', 'Affected Route']
    engineered_cols = [
        'Conflict Score Feature',
        'Shipping Risk',
        'Oil Price Change',
        'Port Congestion Index',
        'Supplier Reliability',
        'Inventory Buffer',
        'Demand Pressure',
        'Transportation Cost Index',
        'Route Availability',
        'Sanction Exposure'
    ]
    
    # Preprocess categorical using saved encoders
    df_processed, _ = preprocess_categorical(df.copy(), categorical_cols, models_dir, 'scenario_encoder.pkl', mode='predict', encoders=encoders)
    
    # Scale numerical using saved scaler
    df_processed, _ = scale_features(df_processed, engineered_cols, models_dir, 'scenario_scaler.pkl', mode='predict', scaler=scaler)
    
    X_cols = engineered_cols + categorical_cols
    X = df_processed[X_cols]
    
    # 3. Predict probabilities of disruption
    probs = clf.predict_proba(X)[:, 1]
    
    # 4. Construct scenario options DataFrame
    scenarios_df = df[['Scenario ID', 'Scenario Name', 'Scenario Type', 'Severity', 'Affected Route']].copy()
    scenarios_df['probability'] = (probs * 100).round(1)
    
    # Strip numeric suffix to get base scenario name for deduplication
    def get_base_name(name):
        parts = name.split(' ')
        if parts and parts[-1].isdigit():
            return ' '.join(parts[:-1])
        return name
    
    scenarios_df['Base Name'] = scenarios_df['Scenario Name'].apply(get_base_name)
    
    # Sort by probability descending, then deduplicate keeping highest prob per base name
    scenarios_sorted = scenarios_df.sort_values(by='probability', ascending=False)
    scenarios_deduped = scenarios_sorted.drop_duplicates(subset='Base Name', keep='first')
    
    # Keep Top 4 unique scenarios
    top_4 = scenarios_deduped.head(4).reset_index(drop=True)
    
    # 5. Display exact output format with colors
    print(Fore.CYAN + "========================================================")
    print(Fore.CYAN + "        SCENARIO SIMULATION RESULTS")
    print(Fore.CYAN + "========================================================")
    print(Fore.GREEN + "\nAvailable Disruption Scenarios\n")
    
    for idx, row in top_4.iterrows():
        print(Fore.YELLOW + f"{idx + 1}. {row['Base Name']}")
        print(Fore.WHITE + f"   Type        : {row['Scenario Type']}")
        print(Fore.WHITE + f"   Severity    : {row['Severity']}")
        print(Fore.WHITE + f"   Probability : {int(row['probability'])}%")
        print()
    
    print(Fore.CYAN + "--------------------------------------------------------")
    
    # 6. Interactive User Prompt
    while True:
        try:
            selection = input("Select Scenario Number : ").strip()
            sel_idx = int(selection) - 1
            if 0 <= sel_idx < 4:
                selected_scenario = top_4.iloc[sel_idx]
                break
            else:
                print("Invalid choice. Please select a number between 1 and 4.")
        except ValueError:
            print("Invalid input. Please enter a valid integer between 1 and 4.")
            
    return selected_scenario['Scenario ID'], selected_scenario['Scenario Name'], selected_scenario['probability']

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_scenario_prediction(base_dir)
