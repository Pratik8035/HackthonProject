import os
from pathlib import Path

# Base Paths
ROOT_DIR = Path(__file__).resolve().parent.parent

# Module Directories
RISK_DIR = ROOT_DIR
ALTERNATIVE_DIR = ROOT_DIR / "Alternative_Supplier_Module"
SCENARIO_DIR = ROOT_DIR / "Scenario_Module"
STRATEGIC_DIR = ROOT_DIR / "StrategicReserveOptimizer"

# Check if paths exist
def verify_paths():
    assert ALTERNATIVE_DIR.exists(), f"Alternative module directory not found at {ALTERNATIVE_DIR}"
    assert SCENARIO_DIR.exists(), f"Scenario module directory not found at {SCENARIO_DIR}"
    assert STRATEGIC_DIR.exists(), f"Strategic module directory not found at {STRATEGIC_DIR}"
