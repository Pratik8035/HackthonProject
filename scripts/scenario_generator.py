"""
scenario_generator.py
=====================
Selects and applies a scenario to the last row of each source dataset.
9 scenarios across 3 risk bands guarantee LOW / MEDIUM / HIGH all appear.
Selection is random-weighted so the same scenario never repeats twice in a row
and the output stays varied across many consecutive runs.
"""

import random
import json
from pathlib import Path
import pandas as pd

try:
    from preprocessing import get_dataset_paths
except Exception:
    BASE_DIR = Path(__file__).resolve().parent.parent
    def get_dataset_paths():
        d = BASE_DIR / "datasets"
        return {
            "news":      d / "news_feed_dataset.csv",
            "shipping":  d / "shipping_ais_dataset.csv",
            "sanctions": d / "sanctions_dataset.csv",
            "oil":       d / "oil_prices_dataset.csv",
        }

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Baseline (LOW risk) ───────────────────────────────────────────────────────
BASELINE = {
    "news":      {"war_event": 0, "terrorism_event": 0, "cyber_attack_event": 0,
                  "political_instability_event": 0, "news_severity": 1.0},
    "shipping":  {"tanker_movements": 30, "shipping_delays": 1,
                  "blocked_routes": 0, "vessel_congestion": 1.5},
    "sanctions": {"country_sanctions": 3, "supplier_sanctions": 10,
                  "export_restrictions": 0, "import_restrictions": 0},
    "oil":       {"crude_price": 78.0, "daily_change": 0.3, "volatility": 1.2},
}


def _load(path):         return pd.read_csv(path)
def _save(df, path):     df.to_csv(path, index=False)

def _apply(df, mods):
    if df.empty:
        return df
    idx = df.index[-1]
    for col, val in mods.items():
        if col in df.columns:
            df.at[idx, col] = val(df.at[idx, col]) if callable(val) else val
    return df

def _reset(paths):
    for key, path in paths.items():
        df = _load(path)
        if not df.empty:
            _save(_apply(df, BASELINE[key]), path)


# ═══════════════════════════════════════════════════════════════════════════════
#  LOW scenarios  (score target: 0–34)
# ═══════════════════════════════════════════════════════════════════════════════

def _low_stable(paths):
    """Completely calm market conditions."""
    _reset(paths)

def _low_minor_shipping(paths):
    """Small port congestion — normal operations overall."""
    _reset(paths)
    p = paths["shipping"]
    _save(_apply(_load(p), {"shipping_delays": 3, "vessel_congestion": 2.5}), p)

def _low_minor_news(paths):
    """Low-level political noise — no operational impact."""
    _reset(paths)
    p = paths["news"]
    _save(_apply(_load(p), {"political_instability_event": 1, "news_severity": 2.5}), p)

def _low_maintenance(paths):
    """Routine pipeline maintenance — slight volatility."""
    _reset(paths)
    p = paths["oil"]
    _save(_apply(_load(p), {"volatility": 1.5}), p)

def _low_currency(paths):
    """Minor currency fluctuations — negligible oil price impact."""
    _reset(paths)
    p = paths["oil"]
    _save(_apply(_load(p), {"daily_change": 0.8, "volatility": 1.8}), p)

def _low_weather(paths):
    """Local shipping weather advisory — minor delay, normal congestion."""
    _reset(paths)
    p = paths["shipping"]
    _save(_apply(_load(p), {"shipping_delays": 2, "vessel_congestion": 2.0}), p)


# ═══════════════════════════════════════════════════════════════════════════════
#  MEDIUM scenarios  (score target: 35–64)
# ═══════════════════════════════════════════════════════════════════════════════

def _medium_oil_spike(paths):
    """Moderate oil price spike with some shipping slowdown."""
    _reset(paths)
    p = paths["oil"]
    _save(_apply(_load(p), {"crude_price": 105.0, "daily_change": 4.5, "volatility": 5.5}), p)
    p = paths["shipping"]
    _save(_apply(_load(p), {"shipping_delays": 7, "vessel_congestion": 4.5,
                             "blocked_routes": 1, "tanker_movements": 22}), p)
    p = paths["news"]
    _save(_apply(_load(p), {"political_instability_event": 1, "news_severity": 4.5}), p)

def _medium_shipping_disruption(paths):
    """Significant route blockage and congestion — moderate supply delay."""
    _reset(paths)
    p = paths["shipping"]
    _save(_apply(_load(p), {"shipping_delays": 10, "vessel_congestion": 5.5,
                             "blocked_routes": 1, "tanker_movements": 18}), p)
    p = paths["oil"]
    _save(_apply(_load(p), {"crude_price": 95.0, "daily_change": 3.0, "volatility": 4.0}), p)
    p = paths["news"]
    _save(_apply(_load(p), {"cyber_attack_event": 1, "news_severity": 4.0}), p)

def _medium_sanctions_pressure(paths):
    """Elevated sanctions with partial trade restrictions."""
    _reset(paths)
    p = paths["sanctions"]
    _save(_apply(_load(p), {"country_sanctions": 18, "supplier_sanctions": 35,
                             "export_restrictions": 1}), p)
    p = paths["oil"]
    _save(_apply(_load(p), {"crude_price": 98.0, "daily_change": 3.8, "volatility": 4.5}), p)
    p = paths["shipping"]
    _save(_apply(_load(p), {"shipping_delays": 8, "vessel_congestion": 4.0,
                             "tanker_movements": 20}), p)
    p = paths["news"]
    _save(_apply(_load(p), {"political_instability_event": 1, "news_severity": 5.0}), p)

def _medium_cyber_harassment(paths):
    """Low-level cyber probing of port infrastructure."""
    _reset(paths)
    p = paths["news"]
    _save(_apply(_load(p), {"cyber_attack_event": 1, "news_severity": 4.2}), p)
    p = paths["shipping"]
    _save(_apply(_load(p), {"shipping_delays": 6, "vessel_congestion": 3.8}), p)

def _medium_regional_unrest(paths):
    """Moderate regional protests near supplier ports."""
    _reset(paths)
    p = paths["news"]
    _save(_apply(_load(p), {"political_instability_event": 1, "news_severity": 4.6}), p)
    p = paths["shipping"]
    _save(_apply(_load(p), {"vessel_congestion": 4.2, "shipping_delays": 5}), p)

def _medium_insurance_hike(paths):
    """Increased maritime transit insurance premiums due to uncertainty."""
    _reset(paths)
    p = paths["oil"]
    _save(_apply(_load(p), {"crude_price": 92.0, "volatility": 5.2}), p)
    p = paths["shipping"]
    _save(_apply(_load(p), {"tanker_movements": 24, "shipping_delays": 6}), p)

def _medium_supplier_downgrade(paths):
    """Compliance issues lead to supplier audit warnings."""
    _reset(paths)
    p = paths["sanctions"]
    _save(_apply(_load(p), {"supplier_sanctions": 28, "export_restrictions": 1}), p)


# ═══════════════════════════════════════════════════════════════════════════════
#  HIGH scenarios  (score target: 65–100)
# ═══════════════════════════════════════════════════════════════════════════════

def _high_geopolitical(paths):
    """Full-scale geopolitical conflict — all signals critical."""
    _reset(paths)
    p = paths["news"]
    _save(_apply(_load(p), {"war_event": 1, "terrorism_event": 1,
                             "political_instability_event": 1, "cyber_attack_event": 1,
                             "news_severity": 10.0}), p)
    p = paths["shipping"]
    _save(_apply(_load(p), {"tanker_movements": 15, "shipping_delays": 20,
                             "vessel_congestion": 9.0, "blocked_routes": 1}), p)
    p = paths["oil"]
    _save(_apply(_load(p), {"crude_price": 135.0, "daily_change": 12.0, "volatility": 9.0}), p)
    p = paths["sanctions"]
    _save(_apply(_load(p), {"country_sanctions": 25, "supplier_sanctions": 45,
                             "export_restrictions": 1, "import_restrictions": 1}), p)

def _high_sanctions_crisis(paths):
    """Major sanctions regime — energy exports blocked, supply chain halted."""
    _reset(paths)
    p = paths["sanctions"]
    _save(_apply(_load(p), {"country_sanctions": 35, "supplier_sanctions": 55,
                             "export_restrictions": 1, "import_restrictions": 1}), p)
    p = paths["shipping"]
    _save(_apply(_load(p), {"tanker_movements": 14, "shipping_delays": 18,
                             "vessel_congestion": 7.0, "blocked_routes": 1}), p)
    p = paths["oil"]
    _save(_apply(_load(p), {"crude_price": 128.0, "daily_change": 11.0, "volatility": 8.0}), p)
    p = paths["news"]
    _save(_apply(_load(p), {"political_instability_event": 1, "terrorism_event": 1,
                             "news_severity": 8.5}), p)

def _high_supply_shock(paths):
    """Extreme oil supply shock — war + blocked straits + sanctions."""
    _reset(paths)
    p = paths["news"]
    _save(_apply(_load(p), {"war_event": 1, "terrorism_event": 1,
                             "news_severity": 9.5}), p)
    p = paths["oil"]
    _save(_apply(_load(p), {"crude_price": 145.0, "daily_change": 14.0, "volatility": 9.5}), p)
    p = paths["shipping"]
    _save(_apply(_load(p), {"tanker_movements": 12, "shipping_delays": 22,
                             "vessel_congestion": 9.5, "blocked_routes": 1}), p)
    p = paths["sanctions"]
    _save(_apply(_load(p), {"country_sanctions": 28, "supplier_sanctions": 50,
                             "export_restrictions": 1}), p)

def _high_cyber_blackout(paths):
    """Critical ransomware attack on national pipelines and port logistics."""
    _reset(paths)
    p = paths["news"]
    _save(_apply(_load(p), {"cyber_attack_event": 1, "news_severity": 9.0}), p)
    p = paths["shipping"]
    _save(_apply(_load(p), {"shipping_delays": 25, "vessel_congestion": 9.0,
                             "blocked_routes": 1, "tanker_movements": 10}), p)
    p = paths["oil"]
    _save(_apply(_load(p), {"volatility": 9.5, "daily_change": 8.0}), p)

def _high_strait_closure(paths):
    """Total military blockade of critical shipping strait."""
    _reset(paths)
    p = paths["shipping"]
    _save(_apply(_load(p), {"blocked_routes": 1, "shipping_delays": 24,
                             "vessel_congestion": 9.8, "tanker_movements": 8}), p)
    p = paths["news"]
    _save(_apply(_load(p), {"war_event": 1, "news_severity": 8.8}), p)
    p = paths["oil"]
    _save(_apply(_load(p), {"crude_price": 142.0, "daily_change": 13.0, "volatility": 8.5}), p)

def _high_supplier_embargo(paths):
    """State-level absolute supplier embargo on critical resources."""
    _reset(paths)
    p = paths["sanctions"]
    _save(_apply(_load(p), {"country_sanctions": 45, "supplier_sanctions": 65,
                             "export_restrictions": 1, "import_restrictions": 1}), p)
    p = paths["oil"]
    _save(_apply(_load(p), {"crude_price": 130.0, "volatility": 8.5}), p)

def _high_climate_event(paths):
    """Category 5 hurricane devastates main regional refining and shipping hub."""
    _reset(paths)
    p = paths["shipping"]
    _save(_apply(_load(p), {"shipping_delays": 26, "vessel_congestion": 9.2, "tanker_movements": 5}), p)
    p = paths["oil"]
    _save(_apply(_load(p), {"crude_price": 122.0, "volatility": 8.0, "daily_change": 9.0}), p)
    p = paths["news"]
    _save(_apply(_load(p), {"news_severity": 7.5}), p)


# ═══════════════════════════════════════════════════════════════════════════════
#  Scenario registry with risk-band labels and selection weights
# ═══════════════════════════════════════════════════════════════════════════════

SCENARIOS = {
    # name                                 : (function,                  band,     weight)
    "Stable Market":                       (_low_stable,                "LOW",    10),
    "Minor Shipping Delay":                (_low_minor_shipping,        "LOW",    8),
    "Low-Level Political Noise":           (_low_minor_news,           "LOW",    7),
    "Routine Pipeline Maintenance":         (_low_maintenance,          "LOW",    6),
    "Minor Currency Fluctuation":          (_low_currency,             "LOW",    6),
    "Local Weather Advisory":              (_low_weather,              "LOW",    6),
    
    "Oil Price Spike":                     (_medium_oil_spike,          "MEDIUM", 10),
    "Shipping Disruption":                 (_medium_shipping_disruption,"MEDIUM", 10),
    "Sanctions Pressure":                  (_medium_sanctions_pressure, "MEDIUM", 10),
    "Cyber Harassment":                    (_medium_cyber_harassment,   "MEDIUM", 8),
    "Regional Unrest":                     (_medium_regional_unrest,    "MEDIUM", 8),
    "Insurance Premium Hike":              (_medium_insurance_hike,     "MEDIUM", 7),
    "Supplier Downgrade":                  (_medium_supplier_downgrade, "MEDIUM", 7),
    
    "Geopolitical Conflict":               (_high_geopolitical,         "HIGH",   10),
    "Sanctions Crisis":                    (_high_sanctions_crisis,     "HIGH",   10),
    "Supply Shock":                        (_high_supply_shock,         "HIGH",   10),
    "Global Cyber Blackout":               (_high_cyber_blackout,       "HIGH",   8),
    "Strait Closure":                      (_high_strait_closure,       "HIGH",   8),
    "Supplier Embargo":                    (_high_supplier_embargo,     "HIGH",   8),
    "Extreme Climate Event":               (_high_climate_event,        "HIGH",   7),
}

SCENARIO_KEYS    = list(SCENARIOS.keys())
SCENARIO_WEIGHTS = [SCENARIOS[k][2] for k in SCENARIO_KEYS]


def generate_scenario() -> str:
    """
    Randomly select a scenario with strict round-robin band balancing:
    - Cycles through LOW → MEDIUM → HIGH (in random order per cycle)
      so that over any 3 consecutive runs each band appears exactly once.
    - Within a band, the exact same scenario never repeats back-to-back.
    Apply its effects to the last row of each dataset CSV.
    Returns the scenario name.
    """
    paths     = get_dataset_paths()
    data_dir  = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    json_path = data_dir / "current_scenario.json"

    # Load history
    last_scenario    = ""
    cycle_queue      = []     # ordered list of bands remaining in this cycle
    if json_path.exists():
        try:
            state         = json.loads(json_path.read_text())
            last_scenario = state.get("last_scenario", "")
            cycle_queue   = state.get("cycle_queue", [])
        except Exception:
            pass

    # If cycle is exhausted, start a fresh shuffled cycle of all 3 bands
    if not cycle_queue:
        cycle_queue = ["LOW", "MEDIUM", "HIGH"]
        random.shuffle(cycle_queue)

    # Take the next band from the queue
    band       = cycle_queue.pop(0)
    candidates = [k for k in SCENARIO_KEYS if SCENARIOS[k][1] == band]

    # Avoid exact back-to-back repeat within the same band
    filtered = [k for k in candidates if k != last_scenario]
    if filtered:
        candidates = filtered

    scenario_name = random.choice(candidates)
    fn, band, _   = SCENARIOS[scenario_name]

    fn(paths)

    json_path.write_text(json.dumps({
        "last_scenario": scenario_name,
        "cycle_queue":   cycle_queue,
    }))

    return scenario_name


if __name__ == "__main__":
    print(f"Scenario applied: {generate_scenario()}")
