# AI Powered Supply Chain Risk Management Dashboard - Module 3

## Project Overview
This module implements the **Alternative Supplier Recommendation** and **Route, Delay, and Cost Analysis** components of the Supply Chain Dashboard. It includes Machine Learning models (XGBoost Ranker and Random Forest Regressors) to predict the best alternative suppliers, logistics costs, and shipment delays, as well as NetworkX for shortest route optimization using Dijkstra's algorithm.

## Folder Structure
```
Alternative Supplier Recommendation/
├── app.py
├── requirements.txt
├── README.md
├── datasets/
│      live_risk_dataset.csv
│      scenario_effects_dataset.csv
│      current_supplier_dataset.csv
│      alternative_supplier_dataset.csv
│      route_dataset.csv
│      delay_dataset.csv
│      cost_dataset.csv
├── models/
│      supplier_ranker.pkl
│      delay_model.pkl
│      cost_model.pkl
├── training/
│      train_supplier_model.py
│      train_delay_model.py
│      train_cost_model.py
├── routes/
│      supplier_api.py
│      analysis_api.py
└── utils/
       preprocessing.py
       route_optimizer.py
```

## Installation
1. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## How to Train Models
The datasets are already provided in the `datasets/` directory. Simply run the following scripts to train and save the machine learning models:
```bash
python training/train_supplier_model.py
python training/train_delay_model.py
python training/train_cost_model.py
```
This will save the `.pkl` files inside the `models/` folder.

## How to Run Flask
Start the backend server by running:
```bash
python app.py
```
The server will start at `http://127.0.0.1:5000`.

## How to Test APIs
You can test the following endpoints using Postman, Insomnia, or cURL:

1. **Get Current Suppliers** (GET)
   `GET http://127.0.0.1:5000/current-suppliers`

2. **Recommend Suppliers** (POST)
   `POST http://127.0.0.1:5000/recommend`
   ```json
   {
       "current_supplier_id": "CUR_001"
   }
   ```

3. **Route Analysis** (POST)
   `POST http://127.0.0.1:5000/route`
   ```json
   {
       "selected_supplier": "UAE Energy Ltd 5"
   }
   ```

4. **Delay Prediction** (POST)
   `POST http://127.0.0.1:5000/delay`
   ```json
   {
       "selected_supplier": "UAE Energy Ltd 5"
   }
   ```

5. **Cost Prediction** (POST)
   `POST http://127.0.0.1:5000/cost`
   ```json
   {
       "selected_supplier": "UAE Energy Ltd 5"
   }
   ```

6. **Complete Analysis** (POST)
   `POST http://127.0.0.1:5000/complete-analysis`
   ```json
   {
       "current_supplier_id": "CUR_001",
       "selected_supplier": "UAE Energy Ltd 5"
   }
   ```
