"""
Strategic Reserve Optimization Agent
Scenario Engine Module

Implements 4 geopolitical/supply disruption scenarios:
1. Strait of Hormuz Closure (Iran-US conflict)
2. Red Sea / Houthi Disruption
3. OPEC 2 MMB/d Production Cut
4. Critical Supplier Failure (Russia + Iraq simultaneous)

Each scenario:
- Applies disruption parameters to the optimizer
- Runs MILP optimization
- Computes delta vs. baseline
- Saves results and generates text report

Author: Strategic Reserve Optimization Team
Date: 2025
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging
import json

from src.optimization.optimizer import SPROptimizer, SUPPLIERS, SPR_LOCATIONS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCENARIOS_DIR = BASE_DIR / "outputs" / "scenarios"
SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)


class ScenarioEngine:
    """
    Geopolitical scenario simulation engine.
    
    Builds parameterized disruption scenarios and runs them through
    the SPROptimizer to quantify economic and security impacts.
    """
    
    def __init__(self, horizon: int = 12):
        self.horizon = horizon
        self.optimizer = SPROptimizer(horizon=horizon)
        self.T = list(range(1, horizon + 1))
        self.baseline_result = None
    
    def _run_baseline(self) -> dict:
        """Run and cache baseline for comparison."""
        if self.baseline_result is None:
            logger.info("Running baseline optimization...")
            self.baseline_result = self.optimizer.run_baseline()
        return self.baseline_result
    
    # -------------------------------------------------------------------------
    # SCENARIO 1: Strait of Hormuz Closure
    # -------------------------------------------------------------------------
    
    def scenario_hormuz_closure(
        self,
        closure_months: list = None,
        price_spike_pct: float = 35.0,
        rerouting_cost_per_bbl: float = 4.0
    ) -> dict:
        """
        Scenario: Strait of Hormuz Closure.
        
        Context: An Iran-US military confrontation leads to closure of the
        Strait of Hormuz for 2-4 months. ~90% of India's Middle East imports
        transit through Hormuz. India must rely on: West Africa (Nigeria),
        Americas (USA), and SPR drawdown.
        
        Impact:
        - Gulf suppliers (Iraq, Saudi, UAE, Kuwait, Iran) fully disrupted for closure_months
        - Oil price spikes 35% during closure, gradually recovers
        - Rerouting around Cape of Good Hope adds $4/bbl shipping cost
        - India must drawdown SPR and source from non-Gulf suppliers
        
        Args:
            closure_months: Which months see closure (default: months 2-5)
            price_spike_pct: Oil price spike percentage during closure
            rerouting_cost_per_bbl: Extra shipping cost (USD/barrel) for Cape rerouting
        """
        if closure_months is None:
            closure_months = [2, 3, 4, 5]  # Months 2-5 of planning horizon
        
        logger.info(f"\n{'='*60}")
        logger.info("SCENARIO 1: Strait of Hormuz Closure")
        logger.info(f"  Closure months: {closure_months}")
        logger.info(f"  Price spike: +{price_spike_pct}%")
        logger.info(f"  Rerouting cost: +${rerouting_cost_per_bbl}/bbl")
        
        # Build disruptions: Gulf suppliers blocked during closure months
        disruptions = {}
        gulf_suppliers = ["Iraq", "Saudi_Arabia", "UAE", "Kuwait", "Iran"]
        
        for supplier in gulf_suppliers:
            disruptions[supplier] = {}
            for t in self.T:
                if t in closure_months:
                    disruptions[supplier][t] = 0.90  # 90% disruption
                elif t in [m + 1 for m in closure_months]:  # 1 month recovery
                    disruptions[supplier][t] = 0.40  # Partial disruption
                else:
                    disruptions[supplier][t] = 0.0
        
        # Price increases during disruption
        base_price = 78.0
        price_spike_per_period = {}
        for t in self.T:
            if t in closure_months:
                price_spike_per_period[t] = base_price * (1 + price_spike_pct / 100)
            elif t in [m + 1 for m in closure_months]:
                price_spike_per_period[t] = base_price * 1.15  # Lingering premium
            else:
                price_spike_per_period[t] = base_price
        
        avg_crisis_price = np.mean([price_spike_per_period[t] for t in self.T])
        
        params = self.optimizer.build_scenario_parameters(
            base_price=avg_crisis_price,
            base_demand_mmt=20.5,
            base_imports_mmt=18.5,
            disruptions=disruptions,
            scenario_name="Hormuz_Closure"
        )
        
        # Override prices per month
        for t in self.T:
            for supplier in self.optimizer.suppliers:
                premium = SUPPLIERS[supplier]["base_price_premium"]
                eff_price = max(30.0, (price_spike_per_period[t] + premium))
                params["price_per_mmt"][t][supplier] = round(eff_price * 7.33 / 1000, 4)
        
        result = self.optimizer.solve_milp(params)
        baseline = self._run_baseline()
        comparison = self.optimizer.compare_with_baseline(result, baseline)
        
        result["comparison_vs_baseline"] = comparison
        result["scenario_description"] = {
            "name": "Strait of Hormuz Closure",
            "trigger": "Iran-US military confrontation",
            "closure_months": closure_months,
            "gulf_disruption_pct": 90,
            "price_spike_pct": price_spike_pct,
            "rerouting_cost_per_bbl": rerouting_cost_per_bbl,
            "key_insight": (
                f"Hormuz closure for {len(closure_months)} months adds "
                f"${comparison['cost_increase_mn_usd']:.0f}M to procurement costs. "
                f"SPR provides {comparison['baseline_avg_coverage_days']:.0f}-day buffer. "
                f"Non-Gulf diversification (Nigeria, USA) critical."
            )
        }
        
        self._save_scenario_result(result, "hormuz_closure")
        return result
    
    # -------------------------------------------------------------------------
    # SCENARIO 2: Red Sea / Houthi Disruption
    # -------------------------------------------------------------------------
    
    def scenario_red_sea_disruption(
        self,
        disruption_months: int = 8,
        shipping_delay_days: float = 15.0,
        cape_rerouting_pct: float = 70.0
    ) -> dict:
        """
        Scenario: Red Sea / Houthi Missile Attacks.
        
        Context: Sustained Houthi attacks on commercial shipping in the Red Sea
        force tankers to reroute around Cape of Good Hope, adding 12-15 days
        transit time and $3-6/barrel in shipping costs.
        
        Impact:
        - Shipping cost increases by ~$4/barrel for Indian imports
        - Transit time increases by 15 days (supply chain delay)
        - No direct supply reduction, but timing and cost impact
        - Price premium for fast-track non-Suez routes
        """
        logger.info(f"\n{'='*60}")
        logger.info("SCENARIO 2: Red Sea / Houthi Disruption")
        logger.info(f"  Duration: {disruption_months} months")
        logger.info(f"  Shipping delay: +{shipping_delay_days} days")
        logger.info(f"  Cape rerouting: {cape_rerouting_pct}%")
        
        # Red Sea disruption: higher shipping costs, slight supply delay
        # Modeled as a price premium on all imports (shipping cost absorbed)
        shipping_premium_per_bbl = (shipping_delay_days / 30) * 2.5  # ~$1.25-2.5/bbl
        shipping_premium_per_mmt = shipping_premium_per_bbl * 7.33 / 1000  # USD million/MMT
        
        base_price = 78.0
        disruptions = {}  # No supplier is directly blocked
        
        params = self.optimizer.build_scenario_parameters(
            base_price=base_price + shipping_premium_per_bbl * 0.5,
            base_demand_mmt=20.5,
            base_imports_mmt=18.5,
            disruptions=disruptions,
            scenario_name="Red_Sea_Disruption"
        )
        
        # Apply shipping premium to all non-Americas, non-Africa suppliers for disruption months
        affected_suppliers = ["Iraq", "Saudi_Arabia", "UAE", "Kuwait", "Iran"]
        for t in range(1, min(disruption_months + 1, self.horizon + 1)):
            for supplier in affected_suppliers:
                params["price_per_mmt"][t][supplier] += shipping_premium_per_mmt
        
        # Effective supply reduction due to delayed deliveries (in-transit inventory effect)
        delay_supply_reduction = 0.12  # 12% effective reduction in months 1-2 due to delay
        for supplier in affected_suppliers:
            disruptions[supplier] = {}
            for t in [1, 2]:  # First 2 months: delayed delivery impact
                disruptions[supplier][t] = delay_supply_reduction
        
        for t in self.T:
            for supplier in affected_suppliers:
                avail = params["supplier_available"][t].get(supplier, 0)
                disrupt = disruptions.get(supplier, {}).get(t, 0)
                params["supplier_available"][t][supplier] = avail * (1 - disrupt)
        
        result = self.optimizer.solve_milp(params)
        baseline = self._run_baseline()
        comparison = self.optimizer.compare_with_baseline(result, baseline)
        
        result["comparison_vs_baseline"] = comparison
        result["scenario_description"] = {
            "name": "Red Sea / Houthi Disruption",
            "trigger": "Sustained Houthi missile/drone attacks on commercial shipping",
            "disruption_months": disruption_months,
            "shipping_delay_days": shipping_delay_days,
            "cape_rerouting_pct": cape_rerouting_pct,
            "shipping_premium_per_bbl": round(shipping_premium_per_bbl, 2),
            "key_insight": (
                f"Red Sea disruption adds ${shipping_premium_per_bbl:.2f}/bbl shipping premium. "
                f"Over {disruption_months} months, total additional cost: "
                f"${comparison['cost_increase_mn_usd']:.0f}M. "
                f"SPR drawdown can bridge the initial 2-month supply delay."
            )
        }
        
        self._save_scenario_result(result, "red_sea_disruption")
        return result
    
    # -------------------------------------------------------------------------
    # SCENARIO 3: OPEC Production Cut
    # -------------------------------------------------------------------------
    
    def scenario_opec_production_cut(
        self,
        cut_mmbd: float = 2.0,
        cut_duration_months: int = 6,
        price_spike_pct: float = 20.0
    ) -> dict:
        """
        Scenario: OPEC+ Coordinated Production Cut.
        
        Context: OPEC+ announces a surprise 2 MMB/d production cut,
        tightening global supply and causing an oil price spike.
        India faces both higher prices and reduced availability from
        OPEC members who are cutting production.
        
        Impact:
        - All OPEC suppliers reduce availability by pro-rata share of 2 MMB/d cut
        - Oil price spikes 15-25% and remains elevated
        - India must accelerate SPR use to buffer demand
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"SCENARIO 3: OPEC {cut_mmbd} MMB/d Production Cut")
        logger.info(f"  Duration: {cut_duration_months} months")
        logger.info(f"  Price spike: +{price_spike_pct}%")
        
        # OPEC total production: ~27 MMB/d → cut = 2/27 ≈ 7.4% per member
        opec_cut_fraction = cut_mmbd / 27.0
        
        opec_members = ["Iraq", "Saudi_Arabia", "UAE", "Kuwait", "Iran", "Nigeria"]
        
        disruptions = {}
        for supplier in opec_members:
            disruptions[supplier] = {}
            for t in range(1, cut_duration_months + 1):
                disruptions[supplier][t] = opec_cut_fraction * 1.1  # Slightly above pro-rata
        
        avg_crisis_price = 78.0 * (1 + price_spike_pct / 100)
        
        params = self.optimizer.build_scenario_parameters(
            base_price=avg_crisis_price,
            base_demand_mmt=20.5,
            base_imports_mmt=18.5,
            disruptions=disruptions,
            scenario_name="OPEC_Production_Cut"
        )
        
        result = self.optimizer.solve_milp(params)
        baseline = self._run_baseline()
        comparison = self.optimizer.compare_with_baseline(result, baseline)
        
        result["comparison_vs_baseline"] = comparison
        result["scenario_description"] = {
            "name": f"OPEC {cut_mmbd} MMB/d Production Cut",
            "trigger": f"OPEC+ surprise {cut_mmbd} MMB/d supply cut announcement",
            "cut_mmbd": cut_mmbd,
            "cut_duration_months": cut_duration_months,
            "price_spike_pct": price_spike_pct,
            "opec_cut_fraction_pct": round(opec_cut_fraction * 100, 1),
            "key_insight": (
                f"A {cut_mmbd} MMB/d OPEC cut raises prices {price_spike_pct}% and reduces "
                f"OPEC member supply by {opec_cut_fraction*100:.1f}%. "
                f"Additional cost: ${comparison['cost_increase_mn_usd']:.0f}M over {cut_duration_months} months. "
                f"Diversification to Russia/USA/West Africa can partially offset."
            )
        }
        
        self._save_scenario_result(result, "opec_production_cut")
        return result
    
    # -------------------------------------------------------------------------
    # SCENARIO 4: Critical Supplier Failure (Russia + Iraq)
    # -------------------------------------------------------------------------
    
    def scenario_supplier_failure(
        self,
        failed_suppliers: dict = None,
        duration_months: int = 6
    ) -> dict:
        """
        Scenario: Critical Supplier Failure.
        
        Context: Russia faces tightening G7 sanctions that effectively block
        Indian refineries from accessing discounted Russian crude (secondary
        sanctions enforcement). Simultaneously, Iraq experiences political
        instability leading to a 30% reduction in export capacity.
        
        India faces a combined ~40% loss of its two largest suppliers.
        
        Args:
            failed_suppliers: Dict of {supplier: disruption_fraction}
            duration_months: Duration of the disruption
        """
        if failed_suppliers is None:
            failed_suppliers = {
                "Russia": 0.80,  # 80% effective block (secondary sanctions)
                "Iraq": 0.30,    # 30% reduction (political instability)
            }
        
        logger.info(f"\n{'='*60}")
        logger.info("SCENARIO 4: Critical Supplier Failure")
        for supplier, fraction in failed_suppliers.items():
            logger.info(f"  {supplier}: {fraction*100:.0f}% disruption for {duration_months} months")
        
        disruptions = {}
        for supplier, fraction in failed_suppliers.items():
            disruptions[supplier] = {}
            for t in range(1, duration_months + 1):
                # Gradual restoration after disruption ends
                if t <= duration_months:
                    disruptions[supplier][t] = fraction
            # Partial recovery months after main disruption
            for t in range(duration_months + 1, min(duration_months + 4, self.horizon + 1)):
                disruptions[supplier][t] = fraction * (1 - (t - duration_months) * 0.25)
        
        # Price premium due to supply tightness
        russia_share_of_india = 0.40  # ~40% of India imports
        iraq_share_of_india = 0.22    # ~22% of India imports
        
        supply_lost_fraction = (
            failed_suppliers.get("Russia", 0) * russia_share_of_india +
            failed_suppliers.get("Iraq", 0) * iraq_share_of_india
        )
        price_premium_pct = supply_lost_fraction * 35  # ~25% price spike for combined failure
        
        avg_crisis_price = 78.0 * (1 + price_premium_pct / 100)
        
        params = self.optimizer.build_scenario_parameters(
            base_price=avg_crisis_price,
            base_demand_mmt=20.5,
            base_imports_mmt=18.5,
            disruptions=disruptions,
            scenario_name="Supplier_Failure_Russia_Iraq"
        )
        
        result = self.optimizer.solve_milp(params)
        baseline = self._run_baseline()
        comparison = self.optimizer.compare_with_baseline(result, baseline)
        
        result["comparison_vs_baseline"] = comparison
        result["scenario_description"] = {
            "name": "Critical Supplier Failure (Russia + Iraq)",
            "trigger": "Secondary sanctions on Russia + Iraq political instability",
            "failed_suppliers": failed_suppliers,
            "duration_months": duration_months,
            "estimated_supply_loss_pct": round(supply_lost_fraction * 100, 1),
            "price_premium_pct": round(price_premium_pct, 1),
            "key_insight": (
                f"Russia+Iraq combined failure removes ~{supply_lost_fraction*100:.0f}% of supply. "
                f"Price premium estimated at {price_premium_pct:.1f}%. "
                f"Cost impact: ${comparison['cost_increase_mn_usd']:.0f}M over {duration_months} months. "
                f"Pivot to Saudi, UAE, USA, West Africa is the resilience strategy."
            )
        }
        
        self._save_scenario_result(result, "supplier_failure")
        return result
    
    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------
    
    def _save_scenario_result(self, result: dict, name: str):
        """Save scenario result to JSON file."""
        out_path = SCENARIOS_DIR / f"scenario_{name}.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"  OK Saved → {out_path}")
    
    def run_all_scenarios(self) -> dict:
        """Run all 4 scenarios + baseline and produce comparison table."""
        logger.info("=" * 70)
        logger.info("Running All Geopolitical Scenarios")
        logger.info("=" * 70)
        
        # Baseline
        baseline = self._run_baseline()
        self._save_scenario_result(baseline, "baseline")
        
        # Scenarios
        s1 = self.scenario_hormuz_closure()
        s2 = self.scenario_red_sea_disruption()
        s3 = self.scenario_opec_production_cut()
        s4 = self.scenario_supplier_failure()
        
        scenarios = [s1, s2, s3, s4]
        
        # Comparison table
        comparison_rows = []
        for s in scenarios:
            comp = s.get("comparison_vs_baseline", {})
            desc = s.get("scenario_description", {})
            comparison_rows.append({
                "scenario": s["scenario_name"].replace("_", " "),
                "total_cost_mn_usd": s["total_cost_mn_usd"],
                "vs_baseline_cost_mn_usd": comp.get("cost_increase_mn_usd", 0),
                "vs_baseline_cost_pct": comp.get("cost_increase_pct", 0),
                "total_shortage_mmt": s["total_shortage_mmt"],
                "avg_coverage_days": s["avg_coverage_days"],
                "min_coverage_days": s["min_coverage_days"],
                "iea_compliant_months": s["iea_compliant_months"],
                "key_insight": desc.get("key_insight", ""),
            })
        
        # Add baseline
        comparison_rows.insert(0, {
            "scenario": "Baseline (No Disruption)",
            "total_cost_mn_usd": baseline["total_cost_mn_usd"],
            "vs_baseline_cost_mn_usd": 0,
            "vs_baseline_cost_pct": 0,
            "total_shortage_mmt": baseline["total_shortage_mmt"],
            "avg_coverage_days": baseline["avg_coverage_days"],
            "min_coverage_days": baseline["min_coverage_days"],
            "iea_compliant_months": baseline["iea_compliant_months"],
            "key_insight": "Normal operating conditions, optimal procurement mix.",
        })
        
        comparison_df = pd.DataFrame(comparison_rows)
        comp_path = SCENARIOS_DIR / "scenario_comparison.csv"
        comparison_df.to_csv(comp_path, index=False)
        
        logger.info(f"\n{'='*70}")
        logger.info("SCENARIO COMPARISON SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(comparison_df[["scenario", "total_cost_mn_usd", 
                                   "vs_baseline_cost_pct", "avg_coverage_days",
                                   "total_shortage_mmt"]].to_string(index=False))
        logger.info(f"\nOK Comparison saved → {comp_path}")
        
        # Save full comparison to JSON
        all_results = {
            "baseline": baseline,
            "hormuz_closure": s1,
            "red_sea_disruption": s2,
            "opec_production_cut": s3,
            "supplier_failure": s4,
            "comparison_table": comparison_rows,
        }
        
        all_path = SCENARIOS_DIR / "all_scenarios.json"
        with open(all_path, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        
        logger.info(f"OK All scenario results → {all_path}")
        
        return all_results


def run_all_scenarios() -> dict:
    """Convenience function for the master pipeline."""
    engine = ScenarioEngine(horizon=12)
    return engine.run_all_scenarios()


if __name__ == "__main__":
    run_all_scenarios()
