import os
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from preprocessing import load_all_datasets, preprocess_categorical
from feature_engineering import engineer_features, scale_features

def train_scenario_classifier(base_dir):
    data_dir = os.path.join(base_dir, 'datasets')
    models_dir = os.path.join(base_dir, 'models')
    
    # 1. Load datasets
    datasets = load_all_datasets(data_dir)
    
    # Merge and build features
    df = engineer_features(datasets)
    
    # Preprocess categoricals (mode='train' fits and saves encoders)
    categorical_cols = ['Scenario Type', 'Severity', 'Affected Region', 'Affected Commodity', 'Affected Route']
    df, encoders = preprocess_categorical(df, categorical_cols, models_dir, 'scenario_encoder.pkl', mode='train')
    
    # Define feature columns (the 10 engineered features)
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
    
    # Combined features list
    X_cols = engineered_cols + categorical_cols
    
    # Target label: 1 if Base Probability >= 0.5 (high likelihood of disruption)
    df['disruption_label'] = (df['Base Probability'] >= 0.5).astype(int)
    y_col = 'disruption_label'
    
    # Scale engineered columns
    df, scaler = scale_features(df, engineered_cols, models_dir, 'scenario_scaler.pkl', mode='train')
    
    X = df[X_cols]
    y = df[y_col]
    
    # Split train/test (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train RandomForestClassifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    


    # Save model
    model_path = os.path.join(models_dir, 'scenario_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(clf, f)



if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    train_scenario_classifier(base_dir)
