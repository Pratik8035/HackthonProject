# Postman API Testing Guide & Collection

This file outlines the end-to-end steps to execute and test the unified Supply Chain Resilience API platform on Postman. It also includes a copyable **Postman Collection v2.1** JSON configuration block at the bottom that you can import directly into Postman.

---

## Step-by-Step E2E Testing Flow in Postman

When testing, run the API endpoints in the following logical sequence to simulate the real-world operational workflow:

### 1. Risk Assessment (Phase 1)
* **Endpoint**: `GET http://127.0.0.1:8080/api/v1/risk/run`
* **Description**: Evaluates daily macro geopolitical, shipping, and pricing metrics to output a general risk score (0-100) and list the top reasons.

### 2. Disruption Scenarios (Phase 2)
* **Endpoint**: `GET http://127.0.0.1:8080/api/v1/scenario/list`
* **Description**: Returns the top 4 active disruption scenarios and their calculated probabilities. Take note of the `scenario_id`, `scenario_name`, and `probability` from the top candidate.

### 3. Downstream Scenario Effects (Phase 2)
* **Endpoint**: `POST http://127.0.0.1:8080/api/v1/scenario/effects`
* **Query Params**:
  - `scenario_id`: (e.g. `24`)
  - `scenario_name`: (e.g. `Major Cyber Attack on Oil Infrastructure`)
  - `probability`: (e.g. `45.2`)
* **Description**: Simulates the specific scenario and calculates downstream delays, costs, price hikes, and supplier capacity.

### 4. Alternative Supplier Recommendations (Phase 3)
* **Endpoint**: `POST http://127.0.0.1:8080/api/v1/supplier/recommend`
* **JSON Body**:
  ```json
  {
    "current_supplier_id": "CUR_001"
  }
  ```
* **Description**: Evaluates the risk score of the current supplier's country and suggests the top 4 alternative replacement candidates.

### 5. Detailed Route, Delay & Cost Projections (Phase 3)
* **Endpoints**: 
  - `POST http://127.0.0.1:8080/api/v1/supplier/route`
  - `POST http://127.0.0.1:8080/api/v1/supplier/delay`
  - `POST http://127.0.0.1:8080/api/v1/supplier/cost`
* **JSON Body**:
  ```json
  {
    "selected_supplier": "UAE Energy Ltd 5"
  }
  ```
* **Description**: Evaluates optimized shipping route (Dijkstra), RandomForest delay day forecasts, and transportation cost projections for the chosen replacement supplier.

### 6. Strategic Petroleum Reserve Drawdown Optimization (Phase 4)
* **Endpoint**: `POST http://127.0.0.1:8080/api/v1/optimize`
* **JSON Body**:
  ```json
  {
    "gap_data": {
      "daily_gap": [30.0, 35.0, 35.0, 25.0, 20.0],
      "horizon": 5,
      "confidence": 0.85
    },
    "demand_data": [
      {"id": "Refinery_A", "daily_demand": [100.0, 100.0, 100.0, 100.0, 100.0], "priority": 2.0},
      {"id": "Refinery_B", "daily_demand": [80.0, 80.0, 80.0, 80.0, 80.0], "priority": 1.5}
    ],
    "spr_data": {
      "current_inventory": 1500.0,
      "max_daily_drawdown": 80.0,
      "min_reserve_level": 500.0
    },
    "procurement_data": {
      "expected_incoming_shipments": [5.0, 5.0, 5.0, 5.0, 5.0],
      "procurement_cost": [85.0, 88.0, 90.0, 92.0, 85.0],
      "replenishment_lead_time": 2
    }
  }
  ```
* **Description**: Feeds all compiled details into the daily MILP solver to output optimal drawdown schedules and spot procurements.

### 7. Unified Orchestration (All Phases Cohesive E2E)
* **Endpoint**: `POST http://127.0.0.1:8080/api/v1/orchestrate`
* **JSON Body**:
  ```json
  {
    "current_supplier_id": "CUR_001",
    "selected_supplier": "UAE Energy Ltd 5",
    "horizon_days": 7
  }
  ```
* **Description**: Triggers all steps concurrently, parameterizes them with Risk Intelligence, and aggregates results in the SPR solver in one single API request.

---

## Postman Importable Collection (JSON)

Copy the JSON block below, open Postman, click **Import** in the top left, go to the **Raw text** or **File** tab, paste it, and click **Import**.

```json
{
  "info": {
    "name": "Supply Chain Resilience API",
    "description": "API collection for testing unified risk assessment, scenario simulation, alternative supplier routing, and daily SPR optimization.",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Home / Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://127.0.0.1:8080/",
          "protocol": "http",
          "host": [
            "127",
            "0",
            "0",
            "1"
          ],
          "port": "8080",
          "path": [
            ""
          ]
        }
      },
      "response": []
    },
    {
      "name": "1. Run Risk Assessment",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://127.0.0.1:8080/api/v1/risk/run",
          "protocol": "http",
          "host": [
            "127",
            "0",
            "0",
            "1"
          ],
          "port": "8080",
          "path": [
            "api",
            "v1",
            "risk",
            "run"
          ]
        }
      },
      "response": []
    },
    {
      "name": "2. Get Scenario Disruption List",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://127.0.0.1:8080/api/v1/scenario/list",
          "protocol": "http",
          "host": [
            "127",
            "0",
            "0",
            "1"
          ],
          "port": "8080",
          "path": [
            "api",
            "v1",
            "scenario",
            "list"
          ]
        }
      },
      "response": []
    },
    {
      "name": "3. Get Scenario Effects",
      "request": {
        "method": "POST",
        "header": [],
        "url": {
          "raw": "http://127.0.0.1:8080/api/v1/scenario/effects?scenario_id=1&scenario_name=Strait of Hormuz Closure&probability=85.5",
          "protocol": "http",
          "host": [
            "127",
            "0",
            "0",
            "1"
          ],
          "port": "8080",
          "path": [
            "api",
            "v1",
            "scenario",
            "effects"
          ],
          "query": [
            {
              "key": "scenario_id",
              "value": "1"
            },
            {
              "key": "scenario_name",
              "value": "Strait of Hormuz Closure"
            },
            {
              "key": "probability",
              "value": "85.5"
            }
          ]
        }
      },
      "response": []
    },
    {
      "name": "4. Get Current Suppliers",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://127.0.0.1:8080/api/v1/supplier/current",
          "protocol": "http",
          "host": [
            "127",
            "0",
            "0",
            "1"
          ],
          "port": "8080",
          "path": [
            "api",
            "v1",
            "supplier",
            "current"
          ]
        }
      },
      "response": []
    },
    {
      "name": "5. Recommend Alternative Supplier",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"current_supplier_id\": \"CUR_001\"\n}"
        },
        "url": {
          "raw": "http://127.0.0.1:8080/api/v1/supplier/recommend",
          "protocol": "http",
          "host": [
            "127",
            "0",
            "0",
            "1"
          ],
          "port": "8080",
          "path": [
            "api",
            "v1",
            "supplier",
            "recommend"
          ]
        }
      },
      "response": []
    },
    {
      "name": "6. Analyze Route",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"selected_supplier\": \"UAE Energy Ltd 5\"\n}"
        },
        "url": {
          "raw": "http://127.0.0.1:8080/api/v1/supplier/route",
          "protocol": "http",
          "host": [
            "127",
            "0",
            "0",
            "1"
          ],
          "port": "8080",
          "path": [
            "api",
            "v1",
            "supplier",
            "route"
          ]
        }
      },
      "response": []
    },
    {
      "name": "7. Predict Delay",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"selected_supplier\": \"UAE Energy Ltd 5\"\n}"
        },
        "url": {
          "raw": "http://127.0.0.1:8080/api/v1/supplier/delay",
          "protocol": "http",
          "host": [
            "127",
            "0",
            "0",
            "1"
          ],
          "port": "8080",
          "path": [
            "api",
            "v1",
            "supplier",
            "delay"
          ]
        }
      },
      "response": []
    },
    {
      "name": "8. Predict Shipping Cost",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"selected_supplier\": \"UAE Energy Ltd 5\"\n}"
        },
        "url": {
          "raw": "http://127.0.0.1:8080/api/v1/supplier/cost",
          "protocol": "http",
          "host": [
            "127",
            "0",
            "0",
            "1"
          ],
          "port": "8080",
          "path": [
            "api",
            "v1",
            "supplier",
            "cost"
          ]
        }
      },
      "response": []
    },
    {
      "name": "9. Run Complete Supplier Analysis",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"current_supplier_id\": \"CUR_001\",\n  \"selected_supplier\": \"UAE Energy Ltd 5\"\n}"
        },
        "url": {
          "raw": "http://127.0.0.1:8080/api/v1/supplier/complete-analysis",
          "protocol": "http",
          "host": [
            "127",
            "0",
            "0",
            "1"
          ],
          "port": "8080",
          "path": [
            "api",
            "v1",
            "supplier",
            "complete-analysis"
          ]
        }
      },
      "response": []
    },
    {
      "name": "10. Strategic Reserve Optimizer (Body Input)",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"gap_data\": {\n    \"daily_gap\": [20.0, 30.0, 40.0, 50.0, 20.0],\n    \"horizon\": 5,\n    \"confidence\": 0.90\n  },\n  \"demand_data\": [\n    {\"id\": \"Refinery_A\", \"daily_demand\": [100.0, 100.0, 100.0, 100.0, 100.0], \"priority\": 1.5},\n    {\"id\": \"Refinery_B\", \"daily_demand\": [50.0, 50.0, 50.0, 50.0, 50.0], \"priority\": 1.0}\n  ],\n  \"spr_data\": {\n    \"current_inventory\": 1500.0,\n    \"max_daily_drawdown\": 80.0,\n    \"min_reserve_level\": 500.0\n  },\n  \"procurement_data\": {\n    \"expected_incoming_shipments\": [0.0, 0.0, 10.0, 10.0, 10.0],\n    \"procurement_cost\": [85.0, 86.0, 90.0, 92.0, 85.0],\n    \"replenishment_lead_time\": 2\n  }\n}"
        },
        "url": {
          "raw": "http://127.0.0.1:8080/api/v1/optimize",
          "protocol": "http",
          "host": [
            "127",
            "0",
            "0",
            "1"
          ],
          "port": "8080",
          "path": [
            "api",
            "v1",
            "optimize"
          ]
        }
      },
      "response": []
    },
    {
      "name": "11. Unified Cohesive Orchestration",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"current_supplier_id\": \"CUR_001\",\n  \"selected_supplier\": \"UAE Energy Ltd 5\",\n  \"horizon_days\": 7\n}"
        },
        "url": {
          "raw": "http://127.0.0.1:8080/api/v1/orchestrate",
          "protocol": "http",
          "host": [
            "127",
            "0",
            "0",
            "1"
          ],
          "port": "8080",
          "path": [
            "api",
            "v1",
            "orchestrate"
          ]
        }
      },
      "response": []
    }
  ]
}
```
