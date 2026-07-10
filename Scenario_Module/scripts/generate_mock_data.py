import os
import pandas as pd
import numpy as np

def generate_all_mock_data(base_path):
    os.makedirs(base_path, exist_ok=True)
    np.random.seed(42)
    
    n_rows = 200
    
    # 14 Real-world Geopolitical Scenarios
    predefined_scenarios = [
        ("Strait of Hormuz Closure", "Geopolitical Conflict", "Critical", "Middle East", "Crude Oil", "Strait of Hormuz"),
        ("Russian Oil Export Sanctions", "Sanctions", "High", "Europe", "Urals Crude", "North Sea Route"),
        ("Red Sea Shipping Attack", "Geopolitical Conflict", "High", "Middle East", "Refined Products", "Bab-el-Mandeb"),
        ("Singapore Port Congestion", "Port Disruption", "Medium", "Asia", "Fuel Oil", "Malacca Strait"),
        ("Suez Canal Blockage", "Logistics", "High", "Egypt", "Crude Oil", "Suez Canal"),
        ("Cyclone in Indian Ocean", "Weather", "High", "Indian Ocean", "LNG", "Indian Ocean Route"),
        ("OPEC Production Cut", "Economic", "High", "Global", "Crude Oil", "Global Routes"),
        ("UAE Port Strike", "Labor Strike", "Medium", "Middle East", "Refined Products", "Jebel Ali Route"),
        ("LNG Terminal Explosion", "Industrial Accident", "High", "North America", "LNG", "Transatlantic Route"),
        ("Iran-Israel Conflict Escalation", "Geopolitical Conflict", "Critical", "Middle East", "Crude & Gas", "Persian Gulf"),
        ("Pakistan Port Strike", "Labor Strike", "Medium", "South Asia", "Refined Products", "Arabian Sea Route"),
        ("Major Cyber Attack on Oil Infrastructure", "Cyber Security", "High", "Global", "Crude & Products", "Pipeline Networks"),
        ("Extreme Weather Disruption", "Weather", "Medium", "North Sea", "Brent Crude", "North Sea Route"),
        ("Global Fuel Price Shock", "Economic", "High", "Global", "Refined Products", "Global Routes")
    ]
    
    # Generate 200 rows by repeating/sampling from these scenarios
    scenario_indices = np.random.choice(len(predefined_scenarios), n_rows)
    
    # 1. scenario_master.csv
    scenario_master_data = []
    for i, idx in enumerate(scenario_indices):
        name, stype, sev, region, commodity, route = predefined_scenarios[idx]
        scenario_master_data.append({
            'Scenario ID': i + 1,
            'Scenario Name': f"{name} {i+1}",
            'Scenario Type': stype,
            'Severity': sev,
            'Affected Region': region,
            'Affected Commodity': commodity,
            'Affected Route': route,
            'Base Probability': round(np.random.uniform(0.1, 0.95), 2)
        })
    scenario_master = pd.DataFrame(scenario_master_data)
    scenario_master.to_csv(os.path.join(base_path, 'scenario_master.csv'), index=False)
    
    # 2. disruption_rules.csv
    disruption_rules_data = []
    route_status_choices = ['Closed', 'Restricted', 'Open']
    for i, idx in enumerate(scenario_indices):
        name, stype, sev, region, commodity, route = predefined_scenarios[idx]
        
        # Base impact metrics based on Severity
        if sev == "Critical":
            sup_red = np.random.uniform(30.0, 50.0)
            delay = np.random.uniform(14.0, 25.0)
            cost_inc = np.random.uniform(25.0, 45.0)
            oil_inc = np.random.uniform(18.0, 35.0)
            inv_red = np.random.uniform(20.0, 40.0)
            dem_imp = np.random.uniform(15.0, 30.0)
            status = 'Closed'
            alt_route = 'Cape of Good Hope'
            weight = np.random.uniform(0.8, 1.0)
            avail = np.random.uniform(50.0, 65.0)
        elif sev == "High":
            sup_red = np.random.uniform(15.0, 35.0)
            delay = np.random.uniform(7.0, 15.0)
            cost_inc = np.random.uniform(15.0, 30.0)
            oil_inc = np.random.uniform(10.0, 20.0)
            inv_red = np.random.uniform(10.0, 25.0)
            dem_imp = np.random.uniform(8.0, 18.0)
            status = 'Restricted'
            alt_route = 'Cape of Good Hope' if 'Strait' in route or 'Suez' in route else 'Alternative Coastal Route'
            weight = np.random.uniform(0.6, 0.8)
            avail = np.random.uniform(65.0, 80.0)
        else: # Medium
            sup_red = np.random.uniform(5.0, 18.0)
            delay = np.random.uniform(2.0, 8.0)
            cost_inc = np.random.uniform(5.0, 16.0)
            oil_inc = np.random.uniform(3.0, 11.0)
            inv_red = np.random.uniform(3.0, 12.0)
            dem_imp = np.random.uniform(2.0, 9.0)
            status = 'Open'
            alt_route = 'None'
            weight = np.random.uniform(0.3, 0.6)
            avail = np.random.uniform(80.0, 95.0)
            
        disruption_rules_data.append({
            'Scenario ID': i + 1,
            'Supply Reduction %': round(sup_red, 2),
            'Expected Delay': round(delay, 1),
            'Transportation Cost Increase %': round(cost_inc, 2),
            'Oil Price Increase %': round(oil_inc, 2),
            'Inventory Reduction %': round(inv_red, 2),
            'Demand Impact %': round(dem_imp, 2),
            'Route Status': status,
            'Alternative Route': alt_route,
            'Risk Weight': round(weight, 2),
            'Supplier Availability %': round(avail, 2)
        })
    disruption_rules = pd.DataFrame(disruption_rules_data)
    disruption_rules.to_csv(os.path.join(base_path, 'disruption_rules.csv'), index=False)
    
    # 3. shipping_routes.csv
    shipping_routes_data = []
    for i, idx in enumerate(scenario_indices):
        name, stype, sev, region, commodity, route = predefined_scenarios[idx]
        status = disruption_rules_data[i]['Route Status']
        alt = disruption_rules_data[i]['Alternative Route']
        shipping_routes_data.append({
            'Scenario ID': i + 1,
            'Origin': 'Middle East Port' if region == 'Middle East' else 'Global Port',
            'Destination': 'Rotterdam' if region == 'Europe' else 'Singapore' if region == 'Asia' else 'US Gulf Coast',
            'Route Name': route,
            'Route Status': status,
            'Distance': float(np.random.randint(2000, 12000)),
            'Transit Time': float(np.random.randint(10, 45)),
            'Alternative Route': alt,
            'Extra Transit Time': float(np.random.randint(5, 18)) if alt != 'None' else 0.0
        })
    shipping_routes = pd.DataFrame(shipping_routes_data)
    shipping_routes.to_csv(os.path.join(base_path, 'shipping_routes.csv'), index=False)
    
    # 4. oil_price_dataset.csv
    oil_price_data = []
    for i in range(n_rows):
        brent = np.random.uniform(70.0, 95.0)
        wti = brent - np.random.uniform(4.0, 7.0)
        oil_price_data.append({
            'Scenario ID': i + 1,
            'Brent Price': round(brent, 2),
            'WTI Price': round(wti, 2),
            'Price Change %': round(np.random.uniform(-3.0, 8.0), 2),
            'Historical Average': round(np.random.uniform(65.0, 80.0), 2)
        })
    oil_price_dataset = pd.DataFrame(oil_price_data)
    oil_price_dataset.to_csv(os.path.join(base_path, 'oil_price_dataset.csv'), index=False)
    
    # 5. supplier_capacity.csv
    supplier_data = []
    countries = ['Saudi Arabia', 'USA', 'Russia', 'UAE', 'Qatar', 'Kuwait', 'Iraq', 'Iran']
    for i in range(n_rows):
        cap = np.random.uniform(1000.0, 5000.0)
        supplier_data.append({
            'Scenario ID': i + 1,
            'Supplier': f"Supplier_{i+1}",
            'Country': np.random.choice(countries),
            'Available Capacity': round(cap * np.random.uniform(0.6, 0.95), 1),
            'Current Capacity': round(cap, 1),
            'Reliability': round(np.random.uniform(70.0, 99.0), 2)
        })
    supplier_capacity = pd.DataFrame(supplier_data)
    supplier_capacity.to_csv(os.path.join(base_path, 'supplier_capacity.csv'), index=False)
    
    # 6. inventory_levels.csv
    inventory_data = []
    for i in range(n_rows):
        curr = np.random.uniform(500.0, 2000.0)
        inventory_data.append({
            'Scenario ID': i + 1,
            'Strategic Reserve': round(curr * np.random.uniform(1.2, 2.5), 1),
            'Current Inventory': round(curr, 1),
            'Safety Stock': round(curr * 0.25, 1),
            'Remaining Days': float(np.random.randint(15, 90))
        })
    inventory_levels = pd.DataFrame(inventory_data)
    inventory_levels.to_csv(os.path.join(base_path, 'inventory_levels.csv'), index=False)
    
    # 7. transportation_cost.csv
    transport_data = []
    for i in range(n_rows):
        ship = np.random.uniform(100.0, 1500.0)
        ins = ship * np.random.uniform(0.05, 0.25)
        fuel = ship * np.random.uniform(0.3, 0.6)
        transport_data.append({
            'Scenario ID': i + 1,
            'Route': predefined_scenarios[scenario_indices[i]][5],
            'Shipping Cost': round(ship, 2),
            'Insurance Cost': round(ins, 2),
            'Fuel Cost': round(fuel, 2),
            'Total Cost': round(ship + ins + fuel, 2)
        })
    transportation_cost = pd.DataFrame(transport_data)
    transportation_cost.to_csv(os.path.join(base_path, 'transportation_cost.csv'), index=False)
    
    # 8. demand_forecast.csv
    demand_data = []
    for i in range(n_rows):
        curr_dem = np.random.uniform(1500.0, 4500.0)
        demand_data.append({
            'Scenario ID': i + 1,
            'Forecast Demand': round(curr_dem * np.random.uniform(0.9, 1.25), 1),
            'Current Demand': round(curr_dem, 1),
            'Demand Growth': round(np.random.uniform(-1.5, 4.5), 2)
        })
    demand_forecast = pd.DataFrame(demand_data)
    demand_forecast.to_csv(os.path.join(base_path, 'demand_forecast.csv'), index=False)
    
    # 9. live_risk_output.csv
    live_risk_data = []
    for i in range(n_rows):
        conflict = np.random.uniform(0.0, 100.0)
        weather = np.random.uniform(0.0, 100.0)
        sanction = np.random.uniform(0.0, 100.0)
        congestion = np.random.uniform(0.0, 100.0)
        risk = (conflict + weather + sanction + congestion) / 4.0
        live_risk_data.append({
            'Scenario ID': i + 1,
            'Current Risk Score': round(risk, 2),
            'Conflict Score': round(conflict, 2),
            'Weather Score': round(weather, 2),
            'Sanction Score': round(sanction, 2),
            'Port Congestion Score': round(congestion, 2)
        })
    live_risk_output = pd.DataFrame(live_risk_data)
    live_risk_output.to_csv(os.path.join(base_path, 'live_risk_output.csv'), index=False)
    


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datasets_dir = os.path.join(base_dir, 'datasets')
    generate_all_mock_data(datasets_dir)
