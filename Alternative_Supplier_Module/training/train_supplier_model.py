import os
import sys
import pandas as pd
import xgboost as xgb
import joblib

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.preprocessing import preprocess_supplier_data

os.makedirs('models', exist_ok=True)

def train():
    print("Loading datasets for Supplier Ranker...")
    alt_df = pd.read_csv('datasets/alternative_supplier_dataset.csv')
    risk_df = pd.read_csv('datasets/live_risk_dataset.csv')
    scen_df = pd.read_csv('datasets/scenario_effects_dataset.csv')
    
    # We simulate a merged dataset that contains all features required by the ranker
    # For training purposes, we randomly assign risk and scenario metrics to alternative suppliers
    n_samples = len(alt_df)
    
    # Randomly sample to create training combinations
    sampled_risk = risk_df.sample(n=n_samples, replace=True).reset_index(drop=True)
    sampled_scen = scen_df.sample(n=n_samples, replace=True).reset_index(drop=True)
    
    train_df = pd.concat([alt_df.reset_index(drop=True), sampled_risk, sampled_scen], axis=1)
    
    # Preprocess
    X, y = preprocess_supplier_data(train_df, is_training=True)
    
    # For XGBRanker we need groups
    group = [len(X)]
    
    print("Training XGBoost Ranker...")
    model = xgb.XGBRanker(
        tree_method='hist',
        objective='rank:ndcg',
        learning_rate=0.1,
        max_depth=5,
        n_estimators=100
    )
    
    model.fit(X, y, group=group)
    
    joblib.dump(model, 'models/supplier_ranker.pkl')
    print("Model saved to models/supplier_ranker.pkl")

if __name__ == "__main__":
    train()
