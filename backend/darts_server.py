"""
Darts Fantasy Auction - Backend Server
Adapted for PDC World Championship 2025/26
"""

from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict
import socketio
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

# Import darts-specific models
from darts_models import (
    DartsPlayer, DartsPlayerCreate,
    DartsCompetition, DartsCompetitionCreate,
    DartsMatch, DartsMatchCreate, DartsMatchResult, MatchStats,
    DartsAuction, DartsAuctionCreate,
    DartsBid, DartsBidCreate,
    Piggyback, PiggybackCreate,
    Wildcard, WildcardClaim,
    UserSquad, UserScore,
    TournamentRound
)

# Import user models from existing models.py
from models import User, UserCreate

# Import services
from darts_scoring_service import DartsScoringService
from piggyback_service import PiggybackService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Create the main app
app = FastAPI(title="Darts Fantasy Auction API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Store active timers and sequence numbers for auction
active_timers = {}
lot_sequences = {}

def get_next_seq(lot_id: str) -> int:
    """Get next sequence number for a lot"""
    if lot_id not in lot_sequences:
        lot_sequences[lot_id] = 0
    lot_sequences[lot_id] += 1
    return lot_sequences[lot_id]

def create_timer_event(lot_id: str, ends_at_ms: int) -> dict:
    """Create standardized timer event data"""
    import time
    return {
        "lotId": lot_id,
        "seq": get_next_seq(lot_id),
        "endsAt": ends_at_ms,
        "serverNow": int(time.time() * 1000)
    }

def sanitize_mongo_doc(doc):
    """Remove MongoDB-specific fields that can't be JSON serialized"""
    from datetime import datetime
    from bson import ObjectId
    
    if doc is None:
        return None
    
    if isinstance(doc, dict):
        # Clean each key/value pair
        clean_doc = {}
        for k, v in doc.items():
            if k == '_id':
                continue  # Skip _id field
            elif isinstance(v, ObjectId):
                clean_doc[k] = str(v)
            elif isinstance(v, datetime):
                clean_doc[k] = v.isoformat()
            elif isinstance(v, dict):
                clean_doc[k] = sanitize_mongo_doc(v)
            elif isinstance(v, list):
                clean_doc[k] = [sanitize_mongo_doc(item) if isinstance(item, dict) else item for item in v]
            else:
                clean_doc[k] = v
        return clean_doc
    
    return doc

# ===== USER ENDPOINTS =====

@api_router.post("/users", response_model=User)
async def create_user(input: UserCreate):
    """Create or get existing user"""
    existing = await db.users.find_one({"email": input.email})
    if existing:
        return User(**existing)
    
    user_obj = User(**input.model_dump())
    await db.users.insert_one(user_obj.model_dump())
    logger.info(f"Created user: {user_obj.email}")
    return user_obj

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user by ID"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

# ===== DARTS PLAYER ENDPOINTS =====

@api_router.get("/darts/players", response_model=List[DartsPlayer])
async def list_players(
    limit: int = 100,
    nationality: Optional[str] = None,
    min_ranking: Optional[int] = None,
    max_ranking: Optional[int] = None
):
    """List darts players with optional filters"""
    query = {}
    
    if nationality:
        query["nationality"] = nationality
    if min_ranking and max_ranking:
        query["pdcRanking"] = {"$gte": min_ranking, "$lte": max_ranking}
    elif min_ranking:
        query["pdcRanking"] = {"$gte": min_ranking}
    elif max_ranking:
        query["pdcRanking"] = {"$lte": max_ranking}
    
    cursor = db.players.find(query).sort("pdcRanking", 1).limit(limit)
    players = await cursor.to_list(length=limit)
    
    return [DartsPlayer(**p) for p in players]

@api_router.get("/darts/players/{player_id}", response_model=DartsPlayer)
async def get_player(player_id: str):
    """Get player by ID"""
    player = await db.players.find_one({"id": player_id})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return DartsPlayer(**player)

@api_router.post("/darts/players", response_model=DartsPlayer)
async def create_player(input: DartsPlayerCreate):
    """Create a new player (admin only in production)"""
    player_obj = DartsPlayer(**input.model_dump())
    await db.players.insert_one(player_obj.model_dump())
    logger.info(f"Created player: {player_obj.name}")
    return player_obj

# ===== DARTS COMPETITION ENDPOINTS =====

@api_router.post("/darts/competitions", response_model=DartsCompetition)
async def create_competition(input: DartsCompetitionCreate):
    """Create a new darts competition"""
    try:
        # Verify commissioner exists
        commissioner = await db.users.find_one({"id": input.commissionerId})
        if not commissioner:
            raise HTTPException(status_code=404, detail="Commissioner not found")
        
        # Verify selected players exist
        if input.selectedPlayers:
            player_count = await db.players.count_documents({
                "id": {"$in": input.selectedPlayers}
            })
            if player_count != len(input.selectedPlayers):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Some selected players not found. Expected {len(input.selectedPlayers)}, found {player_count}"
                )
        
        competition_obj = DartsCompetition(**input.model_dump())
        competition_obj.commissionerName = commissioner["name"]
        
        # Add commissioner as first participant
        competition_obj.participants = [{
            "userId": commissioner["id"],
            "userName": commissioner["name"],
            "userEmail": commissioner["email"],
            "budgetRemaining": competition_obj.budget,
            "playersWon": [],
            "totalSpent": 0.0
        }]
        
        await db.competitions.insert_one(competition_obj.model_dump())
        
        # Create commissioner's user squad
        squad = UserSquad(
            competitionId=competition_obj.id,
            userId=commissioner["id"],
            userName=commissioner["name"],
            budgetRemaining=competition_obj.budget
        )
        await db.user_squads.insert_one(squad.model_dump())
        
        logger.info(f"Created competition: {competition_obj.name} by {commissioner['name']}")
        
        return competition_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating competition: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/darts/competitions", response_model=List[DartsCompetition])
async def list_competitions(
    user_id: Optional[str] = None,
    status: Optional[str] = None
):
    """List competitions, optionally filtered by user or status"""
    query = {}
    
    if status:
        query["status"] = status
    
    if user_id:
        # Find competitions where user is commissioner or participant
        query["$or"] = [
            {"commissionerId": user_id},
            {"participants.userId": user_id}
        ]
    
    cursor = db.competitions.find(query).sort("createdAt", -1)
    competitions = await cursor.to_list(length=None)
    
    return [DartsCompetition(**c) for c in competitions]

@api_router.get("/darts/competitions/{competition_id}", response_model=DartsCompetition)
async def get_competition(competition_id: str):
    """Get competition details"""
    competition = await db.competitions.find_one({"id": competition_id})
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    return DartsCompetition(**competition)

@api_router.post("/darts/competitions/{competition_id}/join")
async def join_competition(competition_id: str, user_data: dict):
    """Join a competition with invite token"""
    try:
        user_id = user_data.get("userId")
        invite_token = user_data.get("inviteToken")
        
        if not user_id or not invite_token:
            raise HTTPException(status_code=400, detail="userId and inviteToken required")
        
        # Verify user exists
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get competition
        competition = await db.competitions.find_one({"id": competition_id})
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        # Verify invite token (case-insensitive)
        if competition["inviteToken"].upper() != invite_token.upper():
            raise HTTPException(status_code=403, detail="Invalid invite token")
        
        # Check if already joined
        participants = competition.get("participants", [])
        logger.info(f"Join attempt - User: {user['name']} ({user_id}), Competition: {competition['name']}")
        logger.info(f"Current participants: {[p['userName'] for p in participants]}")
        
        if any(p["userId"] == user_id for p in participants):
            logger.warning(f"User {user['name']} already in competition")
            raise HTTPException(status_code=400, detail="Already joined this competition")
        
        # Add participant
        participant = {
            "userId": user_id,
            "userName": user["name"],
            "userEmail": user["email"],
            "budgetRemaining": competition["budget"],
            "playersWon": [],
            "totalSpent": 0.0
        }
        
        await db.competitions.update_one(
            {"id": competition_id},
            {"$push": {"participants": participant}}
        )
        
        # Create user squad
        squad = UserSquad(
            competitionId=competition_id,
            userId=user_id,
            userName=user["name"],
            budgetRemaining=competition["budget"]
        )
        await db.user_squads.insert_one(squad.model_dump())
        
        logger.info(f"User {user['name']} joined competition {competition['name']}")
        
        return {"success": True, "message": "Joined competition"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining competition: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/darts/competitions/{competition_id}")
async def delete_competition(competition_id: str, user_data: dict):
    """Delete a competition (commissioner only)"""
    user_id = user_data.get("userId")
    
    competition = await db.competitions.find_one({"id": competition_id})
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    # Verify commissioner
    if competition["commissionerId"] != user_id:
        raise HTTPException(status_code=403, detail="Only commissioner can delete")
    
    # Delete related data
    await db.competitions.delete_one({"id": competition_id})
    await db.user_squads.delete_many({"competitionId": competition_id})
    await db.auctions.delete_many({"competitionId": competition_id})
    await db.matches.delete_many({"competitionId": competition_id})
    await db.user_scores.delete_many({"competitionId": competition_id})
    await db.piggybacks.delete_many({"competitionId": competition_id})
    await db.wildcards.delete_many({"competitionId": competition_id})
    
    logger.info(f"Deleted competition {competition_id}")
    
    return {"success": True, "message": "Competition deleted"}

# ===== DARTS MATCH ENDPOINTS =====

@api_router.post("/darts/competitions/{competition_id}/matches", response_model=DartsMatch)
async def create_match(competition_id: str, input: DartsMatchCreate):
    """Create a match (for manual fixture entry by commissioner)"""
    # Verify competition exists
    competition = await db.competitions.find_one({"id": competition_id})
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    # Verify players exist
    player1 = await db.players.find_one({"id": input.player1Id})
    player2 = await db.players.find_one({"id": input.player2Id})
    
    if not player1 or not player2:
        raise HTTPException(status_code=404, detail="One or both players not found")
    
    match_obj = DartsMatch(
        competitionId=competition_id,
        round=input.round,
        matchDate=input.matchDate,
        player1Id=input.player1Id,
        player1Name=player1["name"],
        player2Id=input.player2Id,
        player2Name=player2["name"]
    )
    
    await db.matches.insert_one(match_obj.model_dump())
    logger.info(f"Created match: {player1['name']} vs {player2['name']}")
    
    return match_obj

@api_router.get("/darts/competitions/{competition_id}/matches", response_model=List[DartsMatch])
async def list_matches(
    competition_id: str,
    round: Optional[str] = None,
    completed: Optional[bool] = None
):
    """List matches for a competition"""
    query = {"competitionId": competition_id}
    
    if round:
        query["round"] = round
    if completed is not None:
        query["completed"] = completed
    
    cursor = db.matches.find(query).sort("matchDate", 1)
    matches = await cursor.to_list(length=None)
    
    return [DartsMatch(**m) for m in matches]

@api_router.post("/darts/competitions/{competition_id}/matches/{match_id}/result")
async def enter_match_result(
    competition_id: str,
    match_id: str,
    result: DartsMatchResult,
    commissioner_data: dict
):
    """
    Commissioner enters match result manually
    Triggers scoring and piggyback logic
    """
    user_id = commissioner_data.get("userId")
    
    # Verify competition and commissioner
    competition = await db.competitions.find_one({"id": competition_id})
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    if competition["commissionerId"] != user_id:
        raise HTTPException(status_code=403, detail="Only commissioner can enter results")
    
    # Get match
    match = await db.matches.find_one({"id": match_id, "competitionId": competition_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if match.get("completed"):
        raise HTTPException(status_code=400, detail="Match already completed")
    
    # Update match with result
    await db.matches.update_one(
        {"id": match_id},
        {"$set": {
            "winnerId": result.winnerId,
            "score": result.score,
            "player1Stats": result.player1Stats.model_dump(),
            "player2Stats": result.player2Stats.model_dump(),
            "completed": True,
            "enteredBy": user_id,
            "enteredAt": datetime.now(timezone.utc)
        }}
    )
    
    # Fetch updated match
    updated_match = await db.matches.find_one({"id": match_id})
    match_obj = DartsMatch(**updated_match)
    
    logger.info(f"Match result entered: {match_obj.player1Name} vs {match_obj.player2Name} - Winner: {result.winnerId}")
    
    # Trigger scoring update for all users in competition
    scoring_service = DartsScoringService(db, competition["scoringRules"])
    participants = competition.get("participants", [])
    
    for participant in participants:
        await scoring_service.update_user_score_for_match(
            competition_id,
            participant["userId"],
            match_obj
        )
    
    # Trigger piggyback logic (Round 1 only)
    piggyback_service = PiggybackService(db)
    await piggyback_service.handle_match_completion(match_obj)
    
    # Emit real-time update via Socket.IO
    await sio.emit('match_completed', {
        "competitionId": competition_id,
        "matchId": match_id,
        "match": match_obj.model_dump()
    }, room=f"competition_{competition_id}")
    
    return {"success": True, "match": match_obj}

# ===== SCORING & LEADERBOARD ENDPOINTS =====

@api_router.get("/darts/competitions/{competition_id}/leaderboard")
async def get_leaderboard(competition_id: str):
    """Get current leaderboard for a competition"""
    competition = await db.competitions.find_one({"id": competition_id})
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    scoring_service = DartsScoringService(db, competition["scoringRules"])
    leaderboard = await scoring_service.get_leaderboard(competition_id)
    
    return {"leaderboard": leaderboard}

@api_router.post("/darts/competitions/{competition_id}/recalculate-scores")
async def recalculate_scores(competition_id: str, commissioner_data: dict):
    """Recalculate all scores (commissioner only, for fixing issues)"""
    user_id = commissioner_data.get("userId")
    
    competition = await db.competitions.find_one({"id": competition_id})
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    if competition["commissionerId"] != user_id:
        raise HTTPException(status_code=403, detail="Only commissioner can recalculate")
    
    scoring_service = DartsScoringService(db, competition["scoringRules"])
    await scoring_service.recalculate_competition_scores(competition_id)
    
    return {"success": True, "message": "Scores recalculated"}

# ===== DARTS AUCTION ENDPOINTS =====

@api_router.post("/darts/competitions/{competition_id}/auction", response_model=DartsAuction)
async def create_auction(competition_id: str, input: DartsAuctionCreate):
    """Create an auction for a competition"""
    # Verify competition exists
    competition = await db.competitions.find_one({"id": competition_id})
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    # Check if auction already exists
    existing = await db.auctions.find_one({"competitionId": competition_id})
    if existing:
        raise HTTPException(status_code=400, detail="Auction already exists for this competition")
    
    # Create player queue from selected players
    selected_players = competition.get("selectedPlayers", [])
    if not selected_players:
        raise HTTPException(status_code=400, detail="No players selected for competition")
    
    auction_obj = DartsAuction(
        competitionId=competition_id,
        bidTimer=input.bidTimer,
        antiSnipeSeconds=input.antiSnipeSeconds,
        playerQueue=selected_players.copy()
    )
    
    await db.auctions.insert_one(auction_obj.model_dump())
    logger.info(f"Created auction for competition {competition_id}")
    
    return auction_obj

@api_router.get("/darts/competitions/{competition_id}/auction", response_model=DartsAuction)
async def get_competition_auction(competition_id: str):
    """Get auction for a competition"""
    auction = await db.auctions.find_one({"competitionId": competition_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    return DartsAuction(**auction)

@api_router.get("/darts/auctions/{auction_id}")
async def get_auction(auction_id: str):
    """Get auction by ID"""
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    return DartsAuction(**auction)

@api_router.post("/darts/auctions/{auction_id}/start")
async def start_auction(auction_id: str, commissioner_data: dict):
    """Start the auction (commissioner only)"""
    try:
        user_id = commissioner_data.get("userId")
        logger.info(f"Starting auction {auction_id} by user {user_id}")
        
        # Get auction
        auction = await db.auctions.find_one({"id": auction_id})
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
        logger.info(f"Auction found, status: {auction['status']}")
        
        # Verify commissioner
        competition = await db.competitions.find_one({"id": auction["competitionId"]})
        if not competition or competition["commissionerId"] != user_id:
            raise HTTPException(status_code=403, detail="Only commissioner can start auction")
        
        if auction["status"] != "pending":
            raise HTTPException(status_code=400, detail="Auction already started")
        
        # Update auction status
        logger.info("Updating auction status to active")
        await db.auctions.update_one(
            {"id": auction_id},
            {"$set": {"status": "active"}}
        )
        
        # Start first lot
        if auction["playerQueue"]:
            first_player_id = auction["playerQueue"][0]
            logger.info(f"Starting first lot for player {first_player_id}")
            await start_lot(auction_id, first_player_id)
        
        logger.info(f"Started auction {auction_id}")
        
        # Emit to all participants
        await sio.emit('auction_started', {
            "auctionId": auction_id,
            "competitionId": auction["competitionId"]
        }, room=f"auction_{auction_id}")
        
        return {"success": True, "message": "Auction started"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting auction {auction_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start auction: {str(e)}")

@api_router.post("/darts/auctions/{auction_id}/pause")
async def pause_auction(auction_id: str, commissioner_data: dict):
    """Pause the auction (commissioner only)"""
    user_id = commissioner_data.get("userId")
    
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Verify commissioner
    competition = await db.competitions.find_one({"id": auction["competitionId"]})
    if not competition or competition["commissionerId"] != user_id:
        raise HTTPException(status_code=403, detail="Only commissioner can pause auction")
    
    if auction["status"] != "active":
        raise HTTPException(status_code=400, detail="Auction is not active")
    
    # Calculate remaining time
    if auction.get("timerEndsAt"):
        remaining_seconds = (auction["timerEndsAt"] - datetime.now(timezone.utc)).total_seconds()
        remaining_seconds = max(0, remaining_seconds)
    else:
        remaining_seconds = auction["bidTimer"]
    
    # Update auction
    await db.auctions.update_one(
        {"id": auction_id},
        {"$set": {
            "status": "paused",
            "pausedRemainingTime": remaining_seconds,
            "pausedAt": datetime.now(timezone.utc)
        }}
    )
    
    # Cancel active timer
    if auction_id in active_timers:
        active_timers[auction_id].cancel()
        del active_timers[auction_id]
    
    logger.info(f"Paused auction {auction_id}")
    
    await sio.emit('auction_paused', {
        "auctionId": auction_id,
        "remainingSeconds": remaining_seconds
    }, room=f"auction_{auction_id}")
    
    return {"success": True, "remainingSeconds": remaining_seconds}

@api_router.post("/darts/auctions/{auction_id}/resume")
async def resume_auction(auction_id: str, commissioner_data: dict):
    """Resume a paused auction (commissioner only)"""
    user_id = commissioner_data.get("userId")
    
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Verify commissioner
    competition = await db.competitions.find_one({"id": auction["competitionId"]})
    if not competition or competition["commissionerId"] != user_id:
        raise HTTPException(status_code=403, detail="Only commissioner can resume auction")
    
    if auction["status"] != "paused":
        raise HTTPException(status_code=400, detail="Auction is not paused")
    
    # Update auction
    remaining_time = auction.get("pausedRemainingTime", auction["bidTimer"])
    new_end_time = datetime.now(timezone.utc) + timedelta(seconds=remaining_time)
    
    await db.auctions.update_one(
        {"id": auction_id},
        {"$set": {
            "status": "active",
            "timerEndsAt": new_end_time,
            "pausedRemainingTime": None,
            "pausedAt": None
        }}
    )
    
    # Restart timer
    lot_id = auction.get("currentLotId")
    if lot_id:
        asyncio.create_task(countdown_timer(auction_id, new_end_time, lot_id))
    
    logger.info(f"Resumed auction {auction_id}")
    
    await sio.emit('auction_resumed', {
        "auctionId": auction_id,
        "endsAt": int(new_end_time.timestamp() * 1000)
    }, room=f"auction_{auction_id}")
    
    return {"success": True, "endsAt": new_end_time}

@api_router.post("/darts/auctions/{auction_id}/bid")
async def place_bid(auction_id: str, bid_input: DartsBidCreate):
    """Place a bid on the current player"""
    try:
        logger.info(f"Bid attempt: user={bid_input.userId}, player={bid_input.playerId}, amount={bid_input.amount}")
        
        # Get auction
        auction = await db.auctions.find_one({"id": auction_id})
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
        if auction["status"] != "active":
            raise HTTPException(status_code=400, detail="Auction is not active")
        
        # Verify player matches current lot
        if bid_input.playerId != auction.get("currentPlayerId"):
            raise HTTPException(status_code=400, detail="Bid is for wrong player")
        
        # Get user and verify budget
        squad = await db.user_squads.find_one({
            "competitionId": auction["competitionId"],
            "userId": bid_input.userId
        })
        
        if not squad:
            raise HTTPException(status_code=404, detail="User squad not found")
        
        if bid_input.amount > squad["budgetRemaining"]:
            raise HTTPException(status_code=400, detail="Insufficient budget")
        
        # Get current highest bid
        highest_bid = await db.bids.find_one({
            "auctionId": auction_id,
            "playerId": bid_input.playerId
        }, sort=[("amount", -1)])
        
        # Validate bid amount (must be higher than current)
        min_bid = highest_bid["amount"] + 1000 if highest_bid else 1000
        if bid_input.amount < min_bid:
            raise HTTPException(status_code=400, detail=f"Bid must be at least {min_bid}")
        
        # Check if user is bidding against themselves
        if highest_bid and highest_bid["userId"] == bid_input.userId:
            raise HTTPException(status_code=400, detail="You already have the highest bid")
        
        # Get user details
        user = await db.users.find_one({"id": bid_input.userId})
        
        # Create bid
        bid_obj = DartsBid(
            auctionId=auction_id,
            userId=bid_input.userId,
            playerId=bid_input.playerId,
            amount=bid_input.amount,
            userName=user["name"] if user else None,
            userEmail=user["email"] if user else None
        )
        
        await db.bids.insert_one(bid_obj.model_dump())
        
        logger.info(f"Bid placed: {bid_input.amount} by {user['name'] if user else bid_input.userId}")
        
        # Anti-snipe logic: extend timer if bid in last X seconds
        timer_ends_at = auction["timerEndsAt"]
        if isinstance(timer_ends_at, datetime) and timer_ends_at.tzinfo is None:
            timer_ends_at = timer_ends_at.replace(tzinfo=timezone.utc)
        
        time_remaining = (timer_ends_at - datetime.now(timezone.utc)).total_seconds()
        lot_id = auction.get("currentLotId")
        
        if time_remaining < auction["antiSnipeSeconds"]:
            new_end_time = datetime.now(timezone.utc) + timedelta(seconds=auction["antiSnipeSeconds"])
            
            await db.auctions.update_one(
                {"id": auction_id},
                {"$set": {"timerEndsAt": new_end_time}}
            )
            
            # Cancel old timer and start new one
            if auction_id in active_timers:
                active_timers[auction_id].cancel()
            
            asyncio.create_task(countdown_timer(auction_id, new_end_time, lot_id))
            
            logger.info(f"Anti-snipe triggered: timer extended to {new_end_time}")
            
            # Emit anti-snipe event with new timer
            await sio.emit('anti_snipe', create_timer_event(lot_id, int(new_end_time.timestamp() * 1000)), room=f"auction_{auction_id}")
        
        # Emit bid event
        await sio.emit('new_bid', {
            "auctionId": auction_id,
            "playerId": bid_input.playerId,
            "amount": bid_input.amount,
            "userId": bid_input.userId,
            "userName": user["name"] if user else "Unknown"
        }, room=f"auction_{auction_id}")
        
        return bid_obj
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing bid: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to place bid: {str(e)}")

# Helper functions for auction flow

async def start_lot(auction_id: str, player_id: str):
    """Start a new lot (player) in the auction"""
    try:
        logger.info(f"start_lot called for auction {auction_id}, player {player_id}")
        
        auction = await db.auctions.find_one({"id": auction_id})
        if not auction:
            logger.error(f"Auction {auction_id} not found in start_lot")
            return
        
        # Get player details
        player = await db.players.find_one({"id": player_id})
        if not player:
            logger.error(f"Player {player_id} not found")
            return
        
        logger.info(f"Found player: {player.get('name')}")
        
        # Create lot ID
        lot_id = str(uuid.uuid4())
        
        # Calculate end time
        end_time = datetime.now(timezone.utc) + timedelta(seconds=auction["bidTimer"])
        logger.info(f"End time calculated: {end_time}")
        
        # Update auction
        logger.info("Updating auction with lot details")
        await db.auctions.update_one(
            {"id": auction_id},
            {"$set": {
                "currentPlayerId": player_id,
                "currentLotId": lot_id,
                "currentLot": auction["currentLot"] + 1,
                "timerEndsAt": end_time
            }}
        )
        
        # Start countdown timer
        logger.info("Creating countdown timer task")
        asyncio.create_task(countdown_timer(auction_id, end_time, lot_id))
        
        logger.info(f"Started lot for player {player['name']}")
        
        # Emit to all participants
        logger.info("Emitting lot_started event")
        await sio.emit('lot_started', {
            "auctionId": auction_id,
            "lotId": lot_id,
            "player": sanitize_mongo_doc(player),
            "endsAt": int(end_time.timestamp() * 1000),
            "timer": create_timer_event(lot_id, int(end_time.timestamp() * 1000))
        }, room=f"auction_{auction_id}")
        
        logger.info("start_lot completed successfully")
        
    except Exception as e:
        logger.error(f"Error in start_lot for auction {auction_id}: {e}", exc_info=True)

async def complete_lot(auction_id: str):
    """Complete the current lot and award player to highest bidder"""
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction or auction["status"] != "active":
        return
    
    current_player_id = auction.get("currentPlayerId")
    if not current_player_id:
        return
    
    # Get highest bid
    highest_bid = await db.bids.find_one({
        "auctionId": auction_id,
        "playerId": current_player_id
    }, sort=[("amount", -1)])
    
    if highest_bid:
        # Award player to winner
        await db.user_squads.update_one(
            {
                "competitionId": auction["competitionId"],
                "userId": highest_bid["userId"]
            },
            {
                "$push": {"playerIds": current_player_id},
                "$inc": {
                    "budgetRemaining": -highest_bid["amount"],
                    "totalSpent": highest_bid["amount"]
                }
            }
        )
        
        logger.info(f"Player {current_player_id} awarded to {highest_bid['userName']} for {highest_bid['amount']}")
        
        # Emit lot sold
        await sio.emit('sold', {
            "auctionId": auction_id,
            "playerId": current_player_id,
            "winnerId": highest_bid["userId"],
            "winnerName": highest_bid["userName"],
            "amount": highest_bid["amount"],
            "unsold": False,
            "winningBid": {
                "userId": highest_bid["userId"],
                "userName": highest_bid["userName"],
                "amount": highest_bid["amount"]
            }
        }, room=f"auction_{auction_id}")
    else:
        # No bids - player goes unsold
        await db.auctions.update_one(
            {"id": auction_id},
            {"$push": {"unsoldPlayers": current_player_id}}
        )
        
        logger.info(f"Player {current_player_id} went unsold")
        
        await sio.emit('sold', {
            "auctionId": auction_id,
            "playerId": current_player_id,
            "unsold": True
        }, room=f"auction_{auction_id}")
    
    # Move to next player
    await start_next_lot(auction_id)

async def start_next_lot(auction_id: str):
    """Start the next lot or complete auction"""
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        return
    
    # Remove current player from queue
    player_queue = auction.get("playerQueue", [])
    if player_queue and auction.get("currentPlayerId") in player_queue:
        player_queue.remove(auction["currentPlayerId"])
        await db.auctions.update_one(
            {"id": auction_id},
            {"$set": {"playerQueue": player_queue}}
        )
    
    # Check if more players to auction
    if player_queue:
        next_player_id = player_queue[0]
        await start_lot(auction_id, next_player_id)
    else:
        # Check if there are unsold players to re-offer
        unsold = auction.get("unsoldPlayers", [])
        if unsold:
            # Re-add unsold players to queue
            await db.auctions.update_one(
                {"id": auction_id},
                {"$set": {
                    "playerQueue": unsold,
                    "unsoldPlayers": []
                }}
            )
            await start_lot(auction_id, unsold[0])
        else:
            # Auction complete
            await db.auctions.update_one(
                {"id": auction_id},
                {"$set": {
                    "status": "completed",
                    "currentPlayerId": None,
                    "currentLotId": None
                }}
            )
            
            logger.info(f"Auction {auction_id} completed")
            
            await sio.emit('auction_complete', {
                "auctionId": auction_id,
                "message": "Auction complete! All players have been auctioned."
            }, room=f"auction_{auction_id}")

async def countdown_timer(auction_id: str, end_time: datetime, lot_id: str):
    """Countdown timer for auction lot"""
    try:
        # Store reference to active timer at the start
        active_timers[auction_id] = asyncio.current_task()
        
        while datetime.now(timezone.utc) < end_time:
            await asyncio.sleep(1)
            
            # Check if auction still active and lot hasn't changed
            auction = await db.auctions.find_one({"id": auction_id})
            if not auction or auction["status"] != "active" or auction.get("currentLotId") != lot_id:
                logger.info(f"Timer cancelled for lot {lot_id}")
                return
            
            # Emit timer tick every second
            remaining = int((end_time - datetime.now(timezone.utc)).total_seconds())
            if remaining <= 10:  # Only emit last 10 seconds to reduce traffic
                import time
                await sio.emit('tick', create_timer_event(lot_id, int(end_time.timestamp() * 1000)), room=f"auction_{auction_id}")
        
        # Time's up - complete the lot
        await complete_lot(auction_id)
        
    except asyncio.CancelledError:
        logger.info(f"Timer task cancelled for auction {auction_id}")
    except Exception as e:
        logger.error(f"Error in countdown timer: {e}")
    finally:
        # Clean up timer reference
        if auction_id in active_timers:
            del active_timers[auction_id]

# ===== PIGGYBACK & WILDCARD ENDPOINTS =====

@api_router.get("/darts/competitions/{competition_id}/users/{user_id}/piggybacks")
async def get_user_piggybacks(competition_id: str, user_id: str):
    """Get piggyback history for a user"""
    piggyback_service = PiggybackService(db)
    piggybacks = await piggyback_service.get_user_piggyback_history(competition_id, user_id)
    
    return {"piggybacks": [p.model_dump() for p in piggybacks]}

@api_router.get("/darts/competitions/{competition_id}/users/{user_id}/wildcard-eligible")
async def check_wildcard_eligibility(competition_id: str, user_id: str):
    """Check if user is eligible to claim wildcard"""
    piggyback_service = PiggybackService(db)
    eligible = await piggyback_service.check_wildcard_eligibility(competition_id, user_id)
    
    if eligible:
        # Get available players
        available_players = await piggyback_service.get_available_wildcard_players(competition_id)
        return {
            "eligible": True,
            "availablePlayers": available_players
        }
    
    return {"eligible": False}

@api_router.post("/darts/competitions/{competition_id}/users/{user_id}/claim-wildcard")
async def claim_wildcard(competition_id: str, user_id: str, claim: WildcardClaim):
    """Claim wildcard for an available player"""
    piggyback_service = PiggybackService(db)
    success = await piggyback_service.claim_wildcard(
        competition_id,
        user_id,
        claim.playerId
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Unable to claim wildcard")
    
    # Emit real-time update
    await sio.emit('wildcard_claimed', {
        "competitionId": competition_id,
        "userId": user_id,
        "playerId": claim.playerId
    }, room=f"competition_{competition_id}")
    
    return {"success": True, "message": "Wildcard claimed"}

# ===== SOCKET.IO EVENT HANDLERS =====

@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def join_auction(sid, data):
    """Join an auction room"""
    auction_id = data.get('auctionId')
    user_id = data.get('userId')
    
    if not auction_id:
        await sio.emit('error', {'message': 'auctionId required'}, room=sid)
        return
    
    # Verify auction exists
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        await sio.emit('error', {'message': 'Auction not found'}, room=sid)
        return
    
    # Join room
    sio.enter_room(sid, f"auction_{auction_id}")
    logger.info(f"User {user_id} joined auction {auction_id}")
    
    # Send current auction state
    current_player = None
    if auction.get("currentPlayerId"):
        current_player = await db.players.find_one({"id": auction.get("currentPlayerId")})
    
    # Get current bids for this player
    current_bids = []
    if auction.get("currentPlayerId"):
        cursor = db.bids.find({
            "auctionId": auction_id,
            "playerId": auction.get("currentPlayerId")
        }).sort("timestamp", -1).limit(10)
        current_bids = await cursor.to_list(length=10)
    
    # Get competition participants with updated budgets
    competition = await db.competitions.find_one({"id": auction.get("competitionId")})
    participants = competition.get("participants", []) if competition else []
    
    # Create timer event if auction is active and has a current lot
    timer_event = None
    if auction.get("status") == "active" and auction.get("currentLotId") and auction.get("timerEndsAt"):
        timer_ends_at = auction["timerEndsAt"]
        if isinstance(timer_ends_at, datetime) and timer_ends_at.tzinfo is None:
            timer_ends_at = timer_ends_at.replace(tzinfo=timezone.utc)
        timer_event = create_timer_event(
            auction.get("currentLotId"),
            int(timer_ends_at.timestamp() * 1000)
        )
    
    # Send sync_state for full synchronization (includes timer for useAuctionClock)
    await sio.emit('sync_state', {
        "auction": sanitize_mongo_doc(auction),
        "currentPlayer": sanitize_mongo_doc(current_player),
        "currentBids": [sanitize_mongo_doc(bid) for bid in current_bids],
        "participants": participants,
        "timer": timer_event
    }, room=sid)
    
    # Also send auction_state for backward compatibility
    await sio.emit('auction_state', {
        "auction": sanitize_mongo_doc(auction),
        "currentPlayer": sanitize_mongo_doc(current_player)
    }, room=sid)

@sio.event
async def leave_auction(sid, data):
    """Leave an auction room"""
    auction_id = data.get('auctionId')
    
    if auction_id:
        sio.leave_room(sid, f"auction_{auction_id}")
        logger.info(f"Client {sid} left auction {auction_id}")

@sio.event
async def join_competition(sid, data):
    """Join a competition room (for leaderboard updates, etc.)"""
    competition_id = data.get('competitionId')
    
    if not competition_id:
        await sio.emit('error', {'message': 'competitionId required'}, room=sid)
        return
    
    sio.enter_room(sid, f"competition_{competition_id}")
    logger.info(f"Client {sid} joined competition {competition_id}")

@sio.event
async def leave_competition(sid, data):
    """Leave a competition room"""
    competition_id = data.get('competitionId')
    
    if competition_id:
        sio.leave_room(sid, f"competition_{competition_id}")
        logger.info(f"Client {sid} left competition {competition_id}")

# Mount the API router
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "darts-fantasy-auction"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8001)
