import os
import sys
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.preprocessing import preprocess_delay_data

os.makedirs('models', exist_ok=True)

def train():
    print("Loading datasets for Delay Model...")
    df = pd.read_csv('datasets/delay_dataset.csv')
    
    X, y = preprocess_delay_data(df, is_training=True)
    
    print("Training Random Forest Regressor for Delay...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    joblib.dump(model, 'models/delay_model.pkl')
    print("Model saved to models/delay_model.pkl")

if __name__ == "__main__":
    train()
