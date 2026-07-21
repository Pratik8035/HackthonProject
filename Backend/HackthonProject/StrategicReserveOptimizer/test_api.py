import requests
import json
from evaluation import get_base_input

input_data = get_base_input(horizon=5)

# Test via standard POST body
print("Testing API via JSON Body...")
response = requests.post("http://localhost:8000/optimize", json=input_data)
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print("Success! Agent returned JSON.")
else:
    print(response.text)

# Test via Header (per explicit user request)
print("\nTesting API via X-Agent-Input Header...")
headers = {
    "X-Agent-Input": json.dumps(input_data)
}
response_header = requests.post("http://localhost:8000/optimize", headers=headers)
print(f"Status Code: {response_header.status_code}")
if response_header.status_code == 200:
    print("Success! Agent returned JSON.")
else:
    print(response_header.text)
