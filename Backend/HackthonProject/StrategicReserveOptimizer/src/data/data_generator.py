"""
Strategic Reserve Optimization Agent
Daily Data Generator Module

Generates historical and current state data at a daily resolution,
including refinery-specific demand, SPR capacities, and overseas supplier availability.

Author: Strategic Reserve Optimization Team
Date: 2025
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Define physical entities
REFINERIES = [
    "IOCL_Panipat", "IOCL_Koyali", "RIL_Jamnagar", "Nayara_Vadinar",
    "BPCL_Kochi", "MRPL_Mangaluru", "CPCL_Chennai"
]

SPR_LOCATIONS = {
    "Vizag": {"capacity_kmt": 1330, "max_draw_kmt_day": 40},
    "Mangaluru": {"capacity_kmt": 1500, "max_draw_kmt_day": 50},
    "Padur": {"capacity_kmt": 2500, "max_draw_kmt_day": 80}
}

SUPPLIERS = ["Iraq", "Saudi_Arabia", "Russia", "UAE", "USA", "Nigeria", "Spot_Market"]

def generate_date_range(days=1095):
    """Generate 3 years of daily data ending at 'today'."""
    end_date = pd.Timestamp.today().normalize()
    start_date = end_date - pd.Timedelta(days=days - 1)
    return pd.date_range(start=start_date, end=end_date, freq='D')

def generate_daily_prices(dates):
    """Generate daily crude oil prices using geometric Brownian motion."""
    np.random.seed(42)
    n = len(dates)
    dt = 1/365.0
    mu = 0.02
    sigma = 0.30
    
    price = np.zeros(n)
    price[0] = 75.0 # Starting price
    
    for i in range(1, n):
        shock = np.random.normal(0, np.sqrt(dt))
        price[i] = price[i-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * shock)
        
        # Mean reversion to $80
        if price[i] > 110: price[i] *= 0.98
        elif price[i] < 50: price[i] *= 1.02
        
    df = pd.DataFrame({"date": dates, "crude_price_usd": np.round(price, 2)})
    return df

def generate_refinery_demand(dates):
    """Generate daily crude requirement for each refinery in kMT."""
    np.random.seed(43)
    n = len(dates)
    
    base_capacities = {
        "IOCL_Panipat": 45.0,     # ~15 MMTPA
        "IOCL_Koyali": 40.0,      # ~13.7 MMTPA
        "RIL_Jamnagar": 180.0,    # ~60 MMTPA
        "Nayara_Vadinar": 60.0,   # ~20 MMTPA
        "BPCL_Kochi": 45.0,       # ~15.5 MMTPA
        "MRPL_Mangaluru": 45.0,   # ~15 MMTPA
        "CPCL_Chennai": 30.0      # ~10.5 MMTPA
    }
    
    data = {"date": dates}
    for ref, cap in base_capacities.items():
        # Seasonal component + random noise + occasional maintenance
        seasonality = 1.0 + 0.05 * np.sin(2 * np.pi * dates.dayofyear.values / 365.0)
        noise = np.random.normal(1.0, 0.02, n)
        daily_demand = cap * seasonality * noise
        
        # Simulate maintenance turnarounds (0% to 50% capacity for 15-30 days)
        for _ in range(2): 
            m_start = np.random.randint(0, n - 30)
            m_len = np.random.randint(15, 30)
            daily_demand[m_start:m_start+m_len] *= np.random.uniform(0.3, 0.7)
            
        data[f"{ref}_demand_kmt"] = np.round(daily_demand, 1)
        
    df = pd.DataFrame(data)
    df["total_demand_kmt"] = df[[f"{r}_demand_kmt" for r in REFINERIES]].sum(axis=1)
    return df

def generate_supplier_availability(dates):
    """Generate available daily export capacity (in kMT) allocated to India."""
    np.random.seed(44)
    n = len(dates)
    
    base_allocations = {
        "Iraq": 120.0,
        "Saudi_Arabia": 100.0,
        "Russia": 150.0,
        "UAE": 60.0,
        "USA": 40.0,
        "Nigeria": 30.0,
        "Spot_Market": 80.0
    }
    
    data = {"date": dates}
    for sup, alloc in base_allocations.items():
        avail = np.random.normal(alloc, alloc * 0.1, n)
        
        # Major geopolitical disruptions
        if sup == "Russia":
            # Sanctions shock
            start = n - 500
            avail[start:start+100] *= 0.4
        elif sup in ["Iraq", "Saudi_Arabia", "UAE"]:
            # Red sea / Hormuz tension
            start = n - 150
            avail[start:start+60] *= 0.6
            
        data[f"{sup}_avail_kmt"] = np.clip(np.round(avail, 1), 0, None)
        
    df = pd.DataFrame(data)
    df["total_avail_kmt"] = df[[f"{s}_avail_kmt" for s in SUPPLIERS]].sum(axis=1)
    return df

def generate_spr_inventory(dates):
    """Generate SPR fill levels."""
    np.random.seed(45)
    n = len(dates)
    
    data = {"date": dates}
    for loc, info in SPR_LOCATIONS.items():
        cap = info["capacity_kmt"]
        # Start at 90% full, drift over time
        fill = np.zeros(n)
        fill[0] = cap * 0.9
        
        for i in range(1, n):
            # Slow random walks for historical SPR usage
            change = np.random.normal(0, cap * 0.005)
            fill[i] = np.clip(fill[i-1] + change, cap * 0.1, cap)
            
        data[f"{loc}_inventory_kmt"] = np.round(fill, 1)
        
    df = pd.DataFrame(data)
    df["total_spr_kmt"] = df[[f"{loc}_inventory_kmt" for loc in SPR_LOCATIONS.keys()]].sum(axis=1)
    return df

def generate_geopolitical_risk(dates):
    """Generate daily risk scores (0-100)."""
    np.random.seed(46)
    n = len(dates)
    
    base_risk = 30 + np.random.normal(0, 5, n)
    # Autoregressive smoothing
    for i in range(1, n):
        base_risk[i] = 0.9 * base_risk[i-1] + 0.1 * base_risk[i]
        
    # Inject spikes
    spikes = [n-500, n-300, n-150, n-30]
    for s in spikes:
        base_risk[s:s+20] += np.random.uniform(30, 50)
        
    risk = np.clip(np.round(base_risk, 1), 0, 100)
    df = pd.DataFrame({"date": dates, "geopolitical_risk_score": risk})
    return df

def generate_all_datasets():
    """Generate and save all daily datasets."""
    logger.info("Generating synthetic daily operational datasets...")
    dates = generate_date_range(1095)
    
    datasets = {
        "prices": generate_daily_prices(dates),
        "refinery_demand": generate_refinery_demand(dates),
        "supplier_availability": generate_supplier_availability(dates),
        "spr_inventory": generate_spr_inventory(dates),
        "geopolitics": generate_geopolitical_risk(dates)
    }
    
    for name, df in datasets.items():
        path = RAW_DATA_DIR / f"daily_{name}.csv"
        df.to_csv(path, index=False)
        logger.info(f"Saved {name} -> {path} (shape: {df.shape})")
        
    logger.info("Daily data generation complete.")
    return True

if __name__ == "__main__":
    generate_all_datasets()
