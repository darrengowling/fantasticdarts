"""
Script to update AuctionRoom.js terminology from league/club to competition/player
"""
import re

# Read the backup file
with open('src/pages/AuctionRoom.js.backup', 'r', encoding='utf-8') as f:
    content = f.read()

# Define replacements in order (specific to general to avoid conflicts)
replacements = [
    # API endpoints first
    (r'/api/leagues/', '/api/darts/competitions/'),
    (r'/api/auction/', '/api/darts/auctions/'),
    (r'`\${API}/clubs`', '`${BACKEND_URL}/darts/players`'),
    (r'/auction/\${auctionId}/clubs', '/darts/auctions/${auctionId}/players'),
    
    # State variables (camelCase)
    (r'\bclubs\b', 'players'),
    (r'\bsetClubs\b', 'setPlayers'),
    (r'\bcurrentClub\b', 'currentPlayer'),
    (r'\bsetCurrentClub\b', 'setCurrentPlayer'),
    (r'\bselectedClubForLot\b', 'selectedPlayerForLot'),
    (r'\bsetSelectedClubForLot\b', 'setSelectedPlayerForLot'),
    (r'\bleague\b', 'competition'),
    (r'\bsetLeague\b', 'setCompetition'),
    (r'\bleagueId\b', 'competitionId'),
    (r'\bleagueResponse\b', 'competitionResponse'),
    
    # Function names
    (r'\bloadClubs\b', 'loadPlayers'),
    
    # Object properties
    (r'\.clubId\b', '.playerId'),
    (r'\.clubsWon\b', '.playersWon'),
    (r'\.clubSlots\b', '.squadSize'),
    (r'\.leagueId\b', '.competitionId'),
    
    # Data properties in responses
    (r'data\.clubs\b', 'data.players'),
    (r'data\.club\b', 'data.player'),
    (r'data\.currentClub\b', 'data.currentPlayer'),
    
    # UI text and labels
    (r'"All Clubs in Auction"', '"All Players in Auction"'),
    (r'"Loading Next Club\.\.\."', '"Loading Next Player..."'),
    (r'Clubs:', 'Players:'),
    (r'Clubs auto-load', 'Players auto-load'),
    (r'Next club', 'Next player'),
    (r'All clubs', 'All players'),
    (r'club: ', 'player: '),
    (r'Club Info', 'Player Info'),
    (r'Club List', 'Player List'),
    (r'Bid History for Current Club', 'Bid History for Current Player'),
    
    # Comments
    (r'# Clubs Overview', '# Players Overview'),
    (r'# Club', '# Player'),
    (r'Reload clubs', 'Reload players'),
    (r'clubs to update', 'players to update'),
    (r'Loaded clubs', 'Loaded players'),
    (r'loading clubs', 'loading players'),
    
    # Messages and alerts
    (r'Re-offering unsold club', 'Re-offering unsold player'),
    (r'Club went unsold', 'Player went unsold'),
    (r'Club sold', 'Player sold'),
    (r'club will be offered', 'player will be offered'),
    (r'clubs have been', 'players have been'),
    
    # Variables in templates
    (r'\{clubs\.', '{players.'),
    (r'\(clubs\.', '(players.'),
    (r'\bclub\.', 'player.'),
    (r'\bclub\)', 'player)'),
    (r' club ', ' player '),
    (r'\(club\)', '(player)'),
    (r'\{club\.', '{player.'),
    
    # CSS classes and test IDs (keep these consistent)
    (r'club-', 'player-'),
    
    # League to Competition
    (r'league to ready', 'competition to ready'),
    (r'isCommissioner = league', 'isCommissioner = competition'),
    
    # Filter callbacks
    (r'\.filter\(\s*c\s*=>', '.filter(p =>'),
    (r'\.map\(\s*\(club\)', '.map((player)'),
    (r'c\.status', 'p.status'),
]

# Apply replacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Write the updated content
with open('src/pages/AuctionRoom.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ AuctionRoom.js updated successfully")
print("Updated terminology:")
print("  - club → player")
print("  - clubs → players")
print("  - league → competition")
print("  - API endpoints updated to /api/darts/...")
