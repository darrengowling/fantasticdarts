"""
Simple test to isolate auction start issue
"""
import requests

BASE_URL = "http://localhost:8001/api"

# Use existing data from previous test
# Get competitions and find one with an auction
response = requests.get(f"{BASE_URL}/darts/competitions")
competitions = response.json()

comp = None
for c in reversed(competitions):
    # Check if this competition has an auction
    response = requests.get(f"{BASE_URL}/darts/competitions/{c['id']}/auction")
    if response.status_code == 200:
        comp = c
        break

if comp:
    print(f"Using competition: {comp['name']} ({comp['id']})")
    
    # Get the auction
    response = requests.get(f"{BASE_URL}/darts/competitions/{comp['id']}/auction")
    if response.status_code == 200:
        auction = response.json()
        print(f"Auction ID: {auction['id']}")
        print(f"Status: {auction['status']}")
        
        # Try to start it if it's pending
        if auction['status'] == 'pending':
            print("\nStarting auction...")
            response = requests.post(
                f"{BASE_URL}/darts/auctions/{auction['id']}/start",
                json={"userId": comp['commissionerId']}
            )
            print(f"Response status: {response.status_code}")
            print(f"Response: {response.text}")
        else:
            print(f"Auction is already {auction['status']}")
    else:
        print(f"No auction found: {response.status_code} - {response.text}")
else:
    print("No competitions found")
