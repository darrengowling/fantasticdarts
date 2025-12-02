"""
Quick API test script
"""
import requests
import json

BASE_URL = "http://localhost:8001/api"

def test_create_user():
    """Test user creation"""
    print("\n1. Testing user creation...")
    response = requests.post(f"{BASE_URL}/users", json={
        "name": "Test Commissioner",
        "email": "test@darts.com"
    })
    print(f"Status: {response.status_code}")
    user = response.json()
    print(f"User created: {user['name']} ({user['id']})")
    return user

def test_list_players():
    """Test listing players"""
    print("\n2. Testing list players...")
    response = requests.get(f"{BASE_URL}/darts/players?limit=5")
    print(f"Status: {response.status_code}")
    players = response.json()
    print(f"Found {len(players)} players:")
    for p in players:
        print(f"  - {p['name']} (Seed {p['seed']})")
    return players

def test_create_competition(user_id, player_ids):
    """Test competition creation"""
    print("\n3. Testing competition creation...")
    response = requests.post(f"{BASE_URL}/darts/competitions", json={
        "name": "Test World Championship 2025",
        "commissionerId": user_id,
        "budget": 100000,
        "squadSize": 8,
        "selectedPlayers": player_ids[:32]  # First 32 players
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        comp = response.json()
        print(f"Competition created: {comp['name']} ({comp['id']})")
        print(f"Invite token: {comp['inviteToken']}")
        return comp
    else:
        print(f"Error: {response.text}")
        return None

def test_list_competitions():
    """Test listing competitions"""
    print("\n4. Testing list competitions...")
    response = requests.get(f"{BASE_URL}/darts/competitions")
    print(f"Status: {response.status_code}")
    comps = response.json()
    print(f"Found {len(comps)} competitions:")
    for c in comps:
        print(f"  - {c['name']} (Status: {c['status']})")
    return comps

if __name__ == "__main__":
    print("=" * 60)
    print("Darts Fantasy API Test")
    print("=" * 60)
    
    try:
        # Test user
        user = test_create_user()
        
        # Test players
        players = test_list_players()
        
        # Get all player IDs
        all_players_response = requests.get(f"{BASE_URL}/darts/players")
        all_players = all_players_response.json()
        player_ids = [p['id'] for p in all_players]
        
        # Test competition
        competition = test_create_competition(user['id'], player_ids)
        
        # Test list competitions
        competitions = test_list_competitions()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
