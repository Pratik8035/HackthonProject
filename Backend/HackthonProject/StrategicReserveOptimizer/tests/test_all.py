import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.data.data_generator import (
    generate_date_range,
    generate_daily_prices,
    generate_spr_inventory,
    generate_supplier_availability,
    generate_geopolitical_risk
)
from src.optimization.optimizer import StrategicReserveOptimizer


class TestDataGenerator:
    """Tests for the daily data generation module."""

    def test_date_range(self):
        dates = generate_date_range(days=100)
        assert len(dates) == 100, "Should generate exactly 100 days"
        assert isinstance(dates, pd.DatetimeIndex), "Should be a DatetimeIndex"

    def test_daily_prices(self):
        dates = generate_date_range(days=50)
        df = generate_daily_prices(dates)
        assert "crude_price_usd" in df.columns
        assert len(df) == 50
        assert df["crude_price_usd"].min() > 20
        assert df["crude_price_usd"].max() < 180

    def test_spr_inventory(self):
        dates = generate_date_range(days=50)
        df = generate_spr_inventory(dates)
        assert "total_spr_kmt" in df.columns
        assert len(df) == 50
        # Check Vizag capacity limits
        assert (df["Vizag_inventory_kmt"] <= 1330).all()

    def test_supplier_availability(self):
        dates = generate_date_range(days=50)
        df = generate_supplier_availability(dates)
        assert "total_avail_kmt" in df.columns
        assert len(df) == 50

    def test_geopolitical_risk(self):
        dates = generate_date_range(days=50)
        df = generate_geopolitical_risk(dates)
        assert "geopolitical_risk_score" in df.columns
        assert (df["geopolitical_risk_score"] >= 0).all()
        assert (df["geopolitical_risk_score"] <= 100).all()


class TestPreprocessorAndFeatures:
    """Tests for preprocessor and feature extraction."""

    def test_preprocessor_runs(self):
        from src.data.preprocessor import merge_and_preprocess, engineer_features
        
        # Test feature engineering on dummy daily df
        dates = pd.date_range(start="2025-01-01", periods=10, freq="D")
        dummy_df = pd.DataFrame({
            "date": dates,
            "crude_price_usd": [75.0] * 10,
            "total_demand_kmt": [400.0] * 10,
            "total_avail_kmt": [500.0] * 10,
            "geopolitical_risk_score": [30.0] * 10
        })
        
        res = engineer_features(dummy_df)
        assert res is True
        
        # Read the written CSV to verify columns
        feat_df = pd.read_csv(BASE_DIR / "data" / "processed" / "daily_features.csv")
        assert "day_of_week" in feat_df.columns
        assert "month" in feat_df.columns
        assert "crude_price_usd_roll_7d_mean" in feat_df.columns


class TestStrategicReserveOptimizer:
    """Tests for the daily MILP optimization engine."""

    def test_optimizer_init(self):
        opt = StrategicReserveOptimizer()
        assert opt.BASE_SHORTAGE_PENALTY == 10.0
        assert opt.SPR_HOLDING_COST == 0.005
        assert opt.INLAND_PIPELINE_COST == 0.02

    def test_optimizer_solve_runs(self):
        opt = StrategicReserveOptimizer()
        
        # Create a simple mock input for 5 days
        mock_input = {
            "gap_data": {
                "daily_gap": [20.0, 30.0, 40.0, 50.0, 20.0],
                "horizon": 5,
                "confidence": 0.90
            },
            "demand_data": [
                {"id": "Refinery_A", "daily_demand": [100.0, 100.0, 100.0, 100.0, 100.0], "priority": 1.5},
                {"id": "Refinery_B", "daily_demand": [50.0, 50.0, 50.0, 50.0, 50.0], "priority": 1.0}
            ],
            "spr_data": {
                "current_inventory": 1500.0,
                "max_daily_drawdown": 80.0,
                "min_reserve_level": 500.0
            },
            "procurement_data": {
                "expected_incoming_shipments": [0.0, 0.0, 10.0, 10.0, 10.0],
                "procurement_cost": [85.0, 86.0, 90.0, 92.0, 85.0],
                "replenishment_lead_time": 2
            }
        }
        
        res = opt.solve(
            gap_data=mock_input["gap_data"],
            demand_data=mock_input["demand_data"],
            spr_data=mock_input["spr_data"],
            procurement_data=mock_input["procurement_data"]
        )
        
        assert "release_spr" in res
        assert "drawdown_schedule" in res
        assert "refinery_allocation" in res
        assert "replenishment_plan" in res
        assert "optimization_score" in res
        
        # Check drawdown limits
        for val in res["drawdown_schedule"]:
            assert val <= 80.0
            
        # Total cost should be non-negative
        assert res["estimated_total_cost"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
