import requests

auction_id = "876cfeab-1018-4c2e-9fca-33d261499702"
response = requests.get(f"http://localhost:8001/api/darts/auctions/{auction_id}")
print(f"Status: {response.status_code}")
print(f"Response text: {response.text}")
if response.status_code == 200:
    data = response.json()
    print(f"\nKeys in response: {list(data.keys())}")
    print(f"\nFull data:")
    import json
    print(json.dumps(data, indent=2, default=str))
