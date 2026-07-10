import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def generate_reasons(shap_df: pd.DataFrame, risk_class: str) -> pd.DataFrame:
    """
    Generate human-readable risk reasons from SHAP values and the latest
    observation in engineered_risk_dataset.csv.

    Parameters
    ----------
    shap_df    : pd.DataFrame  — output of explain_prediction()
    risk_class : str           — 'LOW', 'MEDIUM', or 'HIGH'

    Returns
    -------
    reasons_df : pd.DataFrame  — columns: Reason, Importance, Feature
    """
    dataset_path = BASE_DIR / "datasets" / "engineered_risk_dataset.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Engineered dataset not found at {dataset_path}.")

    df         = pd.read_csv(dataset_path)
    if df.empty:
        raise ValueError("Engineered dataset is empty.")
    latest_row = df.iloc[-1]

    reasons_list = []

    if risk_class == 'LOW':
        reasons_list = [
            {"Reason": "Shipping routes operating normally",
             "Importance": 1.0, "Feature": "Shipping Delay Ratio"},
            {"Reason": "Oil prices remain stable",
             "Importance": 0.9, "Feature": "Oil Price Change %"},
            {"Reason": "No significant geopolitical conflicts detected",
             "Importance": 0.8, "Feature": "Conflict Score"},
            {"Reason": "No new sanctions affecting suppliers",
             "Importance": 0.7, "Feature": "Sanction Exposure"},
        ]
    elif risk_class == 'MEDIUM':
        # Build data-driven medium reasons then fall through to the SHAP block below
        # to populate the list; we just pre-set the class label context.
        for _, row in shap_df.iterrows():
            feature    = row['Feature']
            importance = row['Absolute Importance']
            val        = latest_row.get(feature, 0.0)
            reason     = ""

            if feature == 'Conflict Score':
                is_pol  = latest_row.get('political_instability_event', 0)
                is_cyber= latest_row.get('cyber_attack_event', 0)
                if is_pol == 1:
                    reason = "Regional political tensions affecting supply logistics"
                elif is_cyber == 1:
                    reason = "Cyber incidents disrupting port operations"
                else:
                    reason = "Elevated geopolitical risk in key supply regions"

            elif feature == 'Shipping Delay Ratio':
                delays     = latest_row.get('shipping_delays_raw',
                             latest_row.get('shipping_delays', 0.0))
                congestion = latest_row.get('vessel_congestion_raw',
                             latest_row.get('vessel_congestion', 0.0))
                if delays > 5:
                    reason = f"Moderate shipping delays — {delays:.0f} vessels affected"
                elif congestion > 3.5:
                    reason = "Increased vessel congestion slowing port throughput"
                else:
                    reason = "Above-normal shipping disruptions detected"

            elif feature == 'Sanction Exposure':
                exp_rest = latest_row.get('export_restrictions', 0)
                if exp_rest == 1:
                    reason = "Partial trade restrictions limiting supplier access"
                else:
                    reason = "Rising sanction exposure on key supplier countries"

            elif feature == 'Oil Price Change %':
                change_raw = latest_row.get('daily_change_raw',
                             latest_row.get('daily_change', 0.0))
                if change_raw > 2.0:
                    reason = f"Brent crude up {change_raw:.1f}% — moderate price pressure"
                else:
                    reason = "Oil market volatility elevated above normal levels"

            elif feature == 'Risk Frequency':
                reason = "Recurring supply disruptions observed over the past week"

            elif feature == 'Historical Incident Count':
                reason = "Elevated historical incident rate signals growing exposure"

            else:
                reason = f"Moderate alert on feature {feature}"

            reasons_list.append({
                "Reason":     reason,
                "Importance": round(importance, 4),
                "Feature":    feature,
            })
    else:
        for _, row in shap_df.iterrows():
            feature    = row['Feature']
            importance = row['Absolute Importance']
            val        = latest_row.get(feature, 0.0)
            reason     = ""

            if feature == 'Conflict Score':
                is_war   = latest_row.get('war_event', 0)
                is_terror= latest_row.get('terrorism_event', 0)
                is_pol   = latest_row.get('political_instability_event', 0)
                if is_war == 1:
                    reason = "War reported near Strait of Hormuz"
                elif is_terror == 1:
                    reason = "Military conflict affecting crude oil transportation"
                elif is_pol == 1:
                    reason = "Political instability detected near major oil-producing region"
                else:
                    reason = ("Military conflict affecting crude oil transportation"
                              if risk_class == 'HIGH'
                              else "Minor geopolitical tensions affecting logistics")

            elif feature == 'Shipping Delay Ratio':
                delays     = latest_row.get('shipping_delays_raw',
                             latest_row.get('shipping_delays', 0.0))
                is_blocked = latest_row.get('blocked_routes', 0)
                congestion = latest_row.get('vessel_congestion_raw',
                             latest_row.get('vessel_congestion', 0.0))
                if is_blocked == 1:
                    reason = "Heavy vessel congestion at major shipping route"
                elif delays > 5:
                    reason = f"{delays:.0f} oil tankers delayed"
                elif congestion > 4.0:
                    reason = "Shipping operations delayed due to port congestion"
                else:
                    reason = (f"{delays:.0f} oil tankers delayed"
                              if risk_class == 'HIGH'
                              else "Moderate shipping congestion detected")

            elif feature == 'Sanction Exposure':
                exp_rest = latest_row.get('export_restrictions', 0)
                imp_rest = latest_row.get('import_restrictions', 0)
                countries= latest_row.get('country_sanctions_raw',
                           latest_row.get('country_sanctions', 0.0))
                if exp_rest == 1 or imp_rest == 1:
                    reason = "New sanctions imposed on oil exports"
                elif countries > 5:
                    reason = "International sanctions disrupting fuel supply"
                else:
                    reason = "Trade restrictions affecting crude oil suppliers"

            elif feature == 'Oil Price Change %':
                change_raw = latest_row.get('daily_change_raw',
                             latest_row.get('daily_change', 0.0))
                volatility = latest_row.get('volatility_raw',
                             latest_row.get('volatility', 0.0))
                if change_raw > 2.0:
                    reason = f"Brent crude increased by {val:.0f}%"
                elif volatility > 4.0:
                    reason = "Oil market experiencing high price volatility"
                else:
                    reason = ("Global crude oil prices rising rapidly"
                              if risk_class == 'HIGH'
                              else "Brent crude prices increased slightly")

            elif feature == 'Risk Frequency':
                reason = ("Multiple supply chain disruptions reported this week"
                          if val > 0.5
                          else "Frequent operational disruptions increasing overall risk")

            elif feature == 'Historical Incident Count':
                reason = ("Region has experienced repeated supply chain disruptions"
                          if val > 50
                          else "Historical disruption trend indicates elevated risk")
            else:
                reason = f"Operational alert active on feature {feature}"

            reasons_list.append({
                "Reason":     reason,
                "Importance": round(importance, 4),
                "Feature":    feature,
            })

    reasons_df = pd.DataFrame(reasons_list).sort_values(
        by='Importance', ascending=False
    ).reset_index(drop=True)

    return reasons_df


def print_output_block(risk_class: str, risk_score: int, reasons_df: pd.DataFrame):
    """
    Print the final formatted output block to the console.

    Overall Risk : <Risk Level> (<Risk Score>)

    Top Risk Reasons

    ✓ <Reason 1>
    ...
    """
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print(f"Overall Risk : {risk_class} ({risk_score})")
    print()
    print("Top Risk Reasons")
    print()
    for _, row in reasons_df.head(4).iterrows():
        print(f"✓ {row['Reason']}")


if __name__ == "__main__":
    import sys
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.append(str(scripts_dir))

    from predict_risk import predict_risk
    from shap_explainer import explain_prediction

    risk_class, risk_score = predict_risk()
    shap_df    = explain_prediction()
    reasons_df = generate_reasons(shap_df, risk_class)
    print_output_block(risk_class, risk_score, reasons_df)
