# Terminology Fixes - Football to Darts Migration

## Issues Found

The auction room was displaying football-specific terminology and IDs from the original joeyjoes platform:
1. "UEFA ID" displayed instead of PDC-specific data
2. "All Clubs in Auction" header instead of "All Players in Auction"
3. Variable names using "club" terminology (currentClubBids, etc.)

## Changes Made

### 1. Player Display Information
**Before:**
```jsx
<h3 className="text-3xl font-bold text-gray-900 mb-2">{currentPlayer.name}</h3>
<p className="text-xl text-gray-600">{currentPlayer.country}</p>
<p className="text-sm text-gray-500 mt-2">UEFA ID: {currentPlayer.uefaId}</p>
```

**After:**
```jsx
<h3 className="text-3xl font-bold text-gray-900 mb-2">{currentPlayer.name}</h3>
<p className="text-xl text-gray-600">{currentPlayer.nationality}</p>
{currentPlayer.pdcRanking && (
  <p className="text-sm text-gray-500 mt-2">PDC Ranking: #{currentPlayer.pdcRanking}</p>
)}
{currentPlayer.seed && (
  <p className="text-sm text-gray-500">Seed: #{currentPlayer.seed}</p>
)}
```

### 2. Section Headers
**Before:**
```jsx
<h3 className="text-xl font-bold mb-4 text-gray-900">All Clubs in Auction</h3>
```

**After:**
```jsx
<h3 className="text-xl font-bold mb-4 text-gray-900">All Players in Auction</h3>
```

### 3. Variable Names
**Before:**
```javascript
const currentClubBids = currentPlayer ? bids.filter((b) => b.playerId === currentPlayer.id) : [];
console.log("Current club:", currentPlayer);
```

**After:**
```javascript
const currentPlayerBids = currentPlayer ? bids.filter((b) => b.playerId === currentPlayer.id) : [];
console.log("Current player:", currentPlayer);
```

### 4. All References Updated
- `currentClubBids` → `currentPlayerBids` (7 occurrences)
- `"Current club:"` → `"Current player:"` (console logs)
- `"All Clubs"` → `"All Players"` (UI headers)
- `{currentPlayer.country}` → `{currentPlayer.nationality}`
- `{currentPlayer.uefaId}` → `{currentPlayer.pdcRanking}` and `{currentPlayer.seed}`

## Darts Player Model Fields

From `darts_models.py`, DartsPlayer has these fields:
- `id`: UUID
- `name`: Player name
- `pdcId`: External PDC reference (optional)
- `nationality`: Country
- `pdcRanking`: Current PDC ranking (1-128)
- `seed`: World Championship seeding (1-32 for top seeds)
- `profileImageUrl`: Avatar URL (optional)
- `stats`: Career statistics (optional)

## Display Priority

The player card now shows (in order):
1. **Name** - Large, bold
2. **Nationality** - Subtitle
3. **PDC Ranking** - If available (e.g., "PDC Ranking: #1")
4. **Seed** - If available (e.g., "Seed: #1")

This gives users relevant darts-specific information instead of football data.

## Related Commits

- Commit f6764d9: Replace football terminology with darts
- Commit 7de1a07: Fix clubId → playerId in bid request
- Commit 96e8c88: Align Socket.IO event names

## Testing

To verify the fixes:
1. Start an auction
2. Check player card displays:
   - Player name
   - Nationality (not "country")
   - PDC Ranking (not "UEFA ID")
   - Seed number (if seeded)
3. Check section header says "All Players in Auction"
4. Check browser console logs say "Current player:" not "Current club:"

## Status

✅ **Fixed**: All football terminology replaced with darts-specific terms
✅ **Committed**: Changes pushed to GitHub (commit f6764d9)
✅ **Deployed**: Frontend auto-recompiled

## Files Modified

- `frontend/src/pages/AuctionRoom.js` (17 insertions, 12 deletions)
