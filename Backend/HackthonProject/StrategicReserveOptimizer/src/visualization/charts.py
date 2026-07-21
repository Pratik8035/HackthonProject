"""
Strategic Reserve Optimization Agent
Visualization Module

Generates all static charts and reports from optimization results.
Charts are saved to outputs/charts/ as PNG files.

Author: Strategic Reserve Optimization Team
Date: 2025
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging
import json
import warnings
warnings.filterwarnings("ignore")

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    from matplotlib.patches import FancyBboxPatch
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHARTS_DIR = BASE_DIR / "outputs" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# Dark theme colors
DARK_BG = "#0a0e1a"
PANEL_BG = "#0d1525"
ACCENT_BLUE = "#60a5fa"
ACCENT_PURPLE = "#a78bfa"
ACCENT_GREEN = "#34d399"
ACCENT_AMBER = "#fbbf24"
ACCENT_RED = "#f87171"
TEXT_PRIMARY = "#f0f4f8"
TEXT_SECONDARY = "#94a3b8"
GRID_COLOR = "#1e2d4a"


def setup_dark_style():
    """Configure matplotlib dark theme."""
    if not HAS_MATPLOTLIB:
        return
    plt.rcParams.update({
        "figure.facecolor": DARK_BG,
        "axes.facecolor": PANEL_BG,
        "axes.edgecolor": GRID_COLOR,
        "axes.labelcolor": TEXT_SECONDARY,
        "text.color": TEXT_PRIMARY,
        "xtick.color": TEXT_SECONDARY,
        "ytick.color": TEXT_SECONDARY,
        "grid.color": GRID_COLOR,
        "grid.alpha": 0.5,
        "legend.facecolor": PANEL_BG,
        "legend.edgecolor": GRID_COLOR,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titlecolor": TEXT_PRIMARY,
        "axes.titleweight": "bold",
        "figure.dpi": 120,
    })


def plot_price_history_static(prices_df: pd.DataFrame) -> str:
    """Generate static crude oil price history chart."""
    if not HAS_MATPLOTLIB or prices_df is None:
        return ""
    
    setup_dark_style()
    fig, ax = plt.subplots(figsize=(14, 5))
    fig.patch.set_facecolor(DARK_BG)
    
    ax.fill_between(prices_df["date"], prices_df["india_basket_usd"],
                    alpha=0.15, color=ACCENT_BLUE)
    ax.plot(prices_df["date"], prices_df["india_basket_usd"],
            color=ACCENT_BLUE, linewidth=2, label="India Basket (USD/bbl)")
    ax.plot(prices_df["date"], prices_df["brent_usd"],
            color=ACCENT_PURPLE, linewidth=1.5, linestyle="--", alpha=0.8, label="Brent (USD/bbl)")
    
    # Event markers
    events = {
        pd.Timestamp("2020-04-01"): ("COVID Crash", ACCENT_RED),
        pd.Timestamp("2022-02-01"): ("Russia-Ukraine", ACCENT_AMBER),
        pd.Timestamp("2019-09-01"): ("Aramco Attack", ACCENT_GREEN),
        pd.Timestamp("2023-11-01"): ("Houthi Attacks", ACCENT_RED),
    }
    for date, (label, color) in events.items():
        ax.axvline(x=date, color=color, linestyle=":", alpha=0.6, linewidth=1.5)
        y_pos = prices_df.loc[prices_df["date"] <= date, "india_basket_usd"].iloc[-1] + 5
        ax.annotate(label, xy=(date, y_pos), fontsize=7.5, color=color,
                    ha="center", rotation=0)
    
    ax.set_title("India Crude Oil Basket Price (2015–2025)", pad=15)
    ax.set_ylabel("USD / barrel", color=TEXT_SECONDARY)
    ax.legend(loc="upper left", framealpha=0.8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    path = CHARTS_DIR / "01_crude_oil_prices.png"
    plt.savefig(path, bbox_inches="tight", dpi=120, facecolor=DARK_BG)
    plt.close()
    logger.info(f"  ✓ Saved: {path}")
    return str(path)


def plot_spr_levels_static(spr_df: pd.DataFrame) -> str:
    """Generate static SPR fill level chart."""
    if not HAS_MATPLOTLIB or spr_df is None:
        return ""
    
    setup_dark_style()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
    fig.patch.set_facecolor(DARK_BG)
    
    # Stacked bar chart for SPR stocks
    x = spr_df["date"]
    colors = [ACCENT_BLUE, ACCENT_PURPLE, ACCENT_GREEN]
    bottoms = np.zeros(len(spr_df))
    
    for col, color, label in [
        ("vizag_stock_mmt", ACCENT_BLUE, "Visakhapatnam"),
        ("mangaluru_stock_mmt", ACCENT_PURPLE, "Mangaluru"),
        ("padur_stock_mmt", ACCENT_GREEN, "Padur"),
    ]:
        if col in spr_df.columns:
            ax1.bar(x, spr_df[col], bottom=bottoms, color=color,
                    alpha=0.85, label=label, width=25)
            bottoms += spr_df[col].values
    
    ax1.set_title("SPR Stock Levels by Location (MMT)")
    ax1.set_ylabel("MMT", color=TEXT_SECONDARY)
    ax1.legend(loc="upper right", framealpha=0.8)
    ax1.grid(True, alpha=0.3, axis="y")
    
    # Coverage days
    if "coverage_days" in spr_df.columns:
        ax2.plot(x, spr_df["coverage_days"], color=ACCENT_AMBER, linewidth=2)
        ax2.fill_between(x, spr_df["coverage_days"], alpha=0.15, color=ACCENT_AMBER)
        ax2.axhline(y=90, color=ACCENT_GREEN, linestyle="--", linewidth=1.5,
                    label="IEA 90-day target")
        ax2.set_title("SPR Coverage Days (Oil Imports)")
        ax2.set_ylabel("Days", color=TEXT_SECONDARY)
        ax2.legend(loc="upper right", framealpha=0.8)
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    path = CHARTS_DIR / "02_spr_levels.png"
    plt.savefig(path, bbox_inches="tight", dpi=120, facecolor=DARK_BG)
    plt.close()
    logger.info(f"  ✓ Saved: {path}")
    return str(path)


def plot_scenario_comparison_static(comparison_data: list) -> str:
    """Generate scenario comparison bar chart."""
    if not HAS_MATPLOTLIB or not comparison_data:
        return ""
    
    setup_dark_style()
    df = pd.DataFrame(comparison_data)
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.patch.set_facecolor(DARK_BG)
    fig.suptitle("Geopolitical Scenario Comparison", fontsize=14, 
                  color=TEXT_PRIMARY, fontweight="bold", y=1.02)
    
    scenarios = df["scenario"].str.replace("_", " ").tolist()
    colors = [ACCENT_GREEN, ACCENT_RED, ACCENT_AMBER, "#FF6B35", ACCENT_PURPLE]
    bar_colors = colors[:len(scenarios)]
    
    # Plot 1: Total Cost
    ax1 = axes[0]
    bars = ax1.bar(range(len(scenarios)), df["total_cost_mn_usd"],
                   color=bar_colors, alpha=0.85, edgecolor="#1e3a5f")
    ax1.set_title("12-Month Total Cost ($M)", color=TEXT_PRIMARY)
    ax1.set_ylabel("USD Million", color=TEXT_SECONDARY)
    ax1.set_xticks(range(len(scenarios)))
    ax1.set_xticklabels(scenarios, rotation=25, ha="right", fontsize=8)
    ax1.grid(True, alpha=0.3, axis="y")
    for bar, val in zip(bars, df["total_cost_mn_usd"]):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                  f"${val:.0f}M", ha="center", va="bottom", fontsize=8, color=TEXT_PRIMARY)
    
    # Plot 2: Avg Coverage Days
    ax2 = axes[1]
    bars2 = ax2.bar(range(len(scenarios)), df["avg_coverage_days"],
                    color=bar_colors, alpha=0.85, edgecolor="#1e3a5f")
    ax2.axhline(y=90, color=ACCENT_GREEN, linestyle="--", linewidth=1.5, label="IEA target")
    ax2.set_title("Avg SPR Coverage Days", color=TEXT_PRIMARY)
    ax2.set_ylabel("Days", color=TEXT_SECONDARY)
    ax2.set_xticks(range(len(scenarios)))
    ax2.set_xticklabels(scenarios, rotation=25, ha="right", fontsize=8)
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3, axis="y")
    
    # Plot 3: Shortage
    ax3 = axes[2]
    bars3 = ax3.bar(range(len(scenarios)), df["total_shortage_mmt"],
                    color=bar_colors, alpha=0.85, edgecolor="#1e3a5f")
    ax3.set_title("Total Shortage (MMT)", color=TEXT_PRIMARY)
    ax3.set_ylabel("MMT", color=TEXT_SECONDARY)
    ax3.set_xticks(range(len(scenarios)))
    ax3.set_xticklabels(scenarios, rotation=25, ha="right", fontsize=8)
    ax3.grid(True, alpha=0.3, axis="y")
    
    plt.tight_layout()
    path = CHARTS_DIR / "03_scenario_comparison.png"
    plt.savefig(path, bbox_inches="tight", dpi=120, facecolor=DARK_BG)
    plt.close()
    logger.info(f"  ✓ Saved: {path}")
    return str(path)


def plot_import_concentration_static(imports_df: pd.DataFrame) -> str:
    """Generate import source concentration chart."""
    if not HAS_MATPLOTLIB or imports_df is None:
        return ""
    
    setup_dark_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor(DARK_BG)
    
    # Time series stacked area chart
    supplier_cols = {
        "iraq_mmt": ("Iraq", ACCENT_BLUE),
        "saudi_arabia_mmt": ("Saudi Arabia", ACCENT_PURPLE),
        "russia_mmt": ("Russia", ACCENT_RED),
        "uae_mmt": ("UAE", ACCENT_GREEN),
        "kuwait_mmt": ("Kuwait", ACCENT_AMBER),
        "nigeria_mmt": ("Nigeria", "#fb923c"),
        "usa_mmt": ("USA", "#a3e635"),
    }
    
    bottoms = np.zeros(len(imports_df))
    for col, (label, color) in supplier_cols.items():
        if col in imports_df.columns:
            ax1.fill_between(imports_df["date"],
                              bottoms, bottoms + imports_df[col].values,
                              color=color, alpha=0.8, label=label)
            bottoms += imports_df[col].values
    
    ax1.set_title("India Crude Imports by Source (MMT/month)")
    ax1.set_ylabel("MMT / month", color=TEXT_SECONDARY)
    ax1.legend(loc="upper left", fontsize=8, ncols=2)
    ax1.grid(True, alpha=0.3, axis="y")
    
    # Pie chart for latest 12-month average
    latest = imports_df.tail(12).mean()
    pie_data = {label: latest[col] for col, (label, _) in supplier_cols.items() if col in imports_df.columns}
    colors_pie = [c for _, (_, c) in supplier_cols.items() if _.split("_")[0] + "_mmt" in imports_df.columns or True]
    
    wedges, texts, autotexts = ax2.pie(
        list(pie_data.values()),
        labels=list(pie_data.keys()),
        autopct="%1.1f%%",
        colors=[c for _, c in supplier_cols.values() if _ in ["Iraq", "Saudi Arabia", "Russia", "UAE", "Kuwait", "Nigeria", "USA"]],
        pctdistance=0.8,
        startangle=90
    )
    for text in texts:
        text.set_color(TEXT_SECONDARY)
        text.set_fontsize(8)
    for autotext in autotexts:
        autotext.set_color(TEXT_PRIMARY)
        autotext.set_fontsize(7.5)
    
    ax2.set_title("Import Share (12-Month Avg)", color=TEXT_PRIMARY)
    
    plt.tight_layout()
    path = CHARTS_DIR / "04_import_concentration.png"
    plt.savefig(path, bbox_inches="tight", dpi=120, facecolor=DARK_BG)
    plt.close()
    logger.info(f"  ✓ Saved: {path}")
    return str(path)


def generate_all_charts(data_dir: Path = None, scenarios_dir: Path = None):
    """Generate all static charts."""
    logger.info("=" * 60)
    logger.info("Generating Static Visualization Charts")
    logger.info("=" * 60)
    
    if data_dir is None:
        data_dir = BASE_DIR / "data" / "raw"
    if scenarios_dir is None:
        scenarios_dir = BASE_DIR / "outputs" / "scenarios"
    
    chart_paths = []
    
    # Price history
    price_path = data_dir / "crude_oil_prices.csv"
    if price_path.exists():
        df = pd.read_csv(price_path, parse_dates=["date"])
        p = plot_price_history_static(df)
        if p: chart_paths.append(p)
    
    # SPR levels
    spr_path = data_dir / "spr_data.csv"
    if spr_path.exists():
        df = pd.read_csv(spr_path, parse_dates=["date"])
        p = plot_spr_levels_static(df)
        if p: chart_paths.append(p)
    
    # Import concentration
    imports_path = data_dir / "india_crude_imports.csv"
    if imports_path.exists():
        df = pd.read_csv(imports_path, parse_dates=["date"])
        p = plot_import_concentration_static(df)
        if p: chart_paths.append(p)
    
    # Scenario comparison
    comp_path = scenarios_dir / "scenario_comparison.csv"
    if comp_path.exists():
        df = pd.read_csv(comp_path)
        p = plot_scenario_comparison_static(df.to_dict("records"))
        if p: chart_paths.append(p)
    
    logger.info(f"\n✓ {len(chart_paths)} charts saved to {CHARTS_DIR}")
    return chart_paths


if __name__ == "__main__":
    generate_all_charts()
