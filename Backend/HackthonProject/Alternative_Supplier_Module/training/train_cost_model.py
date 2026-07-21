import os
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

os.makedirs('models', exist_ok=True)

def train():
    print("Loading datasets for Cost Model...")
    df = pd.read_csv('datasets/cost_dataset.csv')
    
    features = ['distance_km', 'transportation_cost', 'insurance_cost', 'fuel_cost', 'logistics_cost']
    X = df[features]
    y = df['total_cost']
    
    print("Training Random Forest Regressor for Cost...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    joblib.dump(model, 'models/cost_model.pkl')
    print("Model saved to models/cost_model.pkl")

if __name__ == "__main__":
    train()
