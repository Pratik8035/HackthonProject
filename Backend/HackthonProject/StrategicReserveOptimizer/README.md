# Strategic Reserve Daily Optimization Agent

A pure Python backend module that acts as an AI-powered Strategic Petroleum Reserve (SPR) Optimization Agent. This system calculates the mathematically optimal **daily** SPR drawdown schedule, overseas procurement strategy, and refinery-wise crude oil allocation to minimize supply shortages, logistical bottlenecks, and procurement costs.

## 🌟 Overview

The agent is designed to run silently as a backend optimization engine using **Google OR-Tools** (SCIP/CBC solver). It takes in a daily state dictionary describing the current energy supply situation and outputs a highly detailed, day-by-day procurement and SPR release schedule.

**What it does NOT include:**
- No Dashboard / Frontend
- No REST API / Web Server
- No Database dependencies
- No Cloud / Docker infrastructure

It is a lightweight, high-performance mathematical modeling module.

## 🛠️ Installation

```bash
# Clone the repository
git clone <repo-url>
cd StrategicReserveOptimizer

# Install lightweight dependencies
pip install -r requirements.txt
```

## 🚀 Usage

The agent is encapsulated in a single, reusable class `StrategicReserveAgent` within `agent.py`.

```python
from agent import StrategicReserveAgent
import json

# Initialize the agent with a planning horizon (e.g., 7 days)
agent = StrategicReserveAgent(horizon_days=7)

# Define the current daily supply chain state
current_state = {
    "current_spr_inventory": {"Vizag": 1330.0, "Mangaluru": 1500.0, "Padur": 2500.0},
    "forecasted_prices": [80.0, 81.0, 82.0, 85.0, 90.0, 95.0, 100.0],
    "max_port_throughput": 400.0, # kMT/day limit
    "forecasted_demand": {
        "IOCL_Panipat": [50.0]*7,
        "RIL_Jamnagar": [180.0]*7,
        # ... include all 7 major refineries
    },
    "forecasted_supplier_avail": {
        "Iraq": [100.0]*7,
        "Saudi_Arabia": [100.0]*7,
        # ... include all 7 major suppliers
    },
    "geopolitical_disruption_level": 30.0
}

# Run the optimization
recommendation = agent.optimize(current_state)

# Output JSON
print(json.dumps(recommendation, indent=2))
```

## 📊 Evaluation & Testing

We provide a robust evaluation script that tests the agent against various geopolitical and logistical disruption scenarios (e.g., Strait of Hormuz closure, Port strikes, Supplier failure).

To run the evaluations:
```bash
python evaluation.py
```
*Results will be saved to `outputs/evaluation_results.json`.*

## 🧠 Architecture
1.  **Data Generator**: Synthesizes historically accurate daily crude prices, port congestions, and refinery demands.
2.  **Machine Learning**: `XGBoost` and `LightGBM` modules included for predicting next-day spot prices and supply deficits.
3.  **OR-Tools Optimizer**: The core MILP engine computing the exact day-to-day SPR release schedules and refinery routing.
