from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
from enum import Enum

# Tournament Round Enum
class TournamentRound(str, Enum):
    ROUND_1 = "round_1"  # Round of 128
    ROUND_2 = "round_2"  # Round of 64
    ROUND_3 = "round_3"  # Round of 32
    ROUND_4 = "round_4"  # Round of 16
    QUARTER_FINAL = "quarter_final"
    SEMI_FINAL = "semi_final"
    FINAL = "final"

# Darts Player Models
class DartsPlayer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    pdcId: Optional[str] = None  # External PDC reference
    nationality: str
    pdcRanking: int
    seed: Optional[int] = None  # World Championship seeding (1-32 for top seeds)
    profileImageUrl: Optional[str] = None
    stats: Optional[Dict] = None  # Career stats: 180s, averages, titles
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DartsPlayerCreate(BaseModel):
    name: str
    nationality: str
    pdcRanking: int
    seed: Optional[int] = None
    profileImageUrl: Optional[str] = None

# Darts Competition Models
class DartsCompetition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    commissionerId: str
    commissionerName: Optional[str] = None
    tournamentType: str = "pdc_world_championship"  # Default to World Championship
    budget: float = 100000.0  # Virtual currency budget
    squadSize: int = 8  # Configurable based on participant count
    selectedPlayers: List[str] = []  # List of player IDs (32 for top seeds)
    participants: List[Dict] = []  # {userId, userName, userEmail, budgetRemaining, playersWon, totalSpent}
    status: str = "pending"  # pending, auction_ready, auction_active, tournament_active, completed
    inviteToken: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    scoringRules: Dict = Field(default_factory=lambda: {
        "round_progression": {
            "round_1": 10,
            "round_2": 15,
            "round_3": 25,
            "round_4": 40,
            "quarter_final": 80,
            "semi_final": 150,
            "final": 200,
            "winner": 300
        },
        "performance_bonuses": {
            "180s": 5,  # Per 180 scored
            "legs_won": 2,  # Per leg won
            "match_win": 10,  # Bonus for winning match
            "high_checkout_140_plus": 10,  # High checkout bonus
            "avg_100_plus": 15  # 3-dart average 100+
        }
    })
    tournamentStartDate: datetime = Field(default_factory=lambda: datetime(2025, 12, 11))
    tournamentEndDate: datetime = Field(default_factory=lambda: datetime(2026, 1, 3))
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DartsCompetitionCreate(BaseModel):
    name: str
    commissionerId: str
    budget: float = 100000.0
    squadSize: int = 8
    selectedPlayers: List[str] = []

# Darts Match Models
class MatchStats(BaseModel):
    oneEighties: int = 0  # Number of 180s
    threeDartAverage: float = 0.0
    legsWon: int = 0
    highCheckout: int = 0

class DartsMatch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    competitionId: str
    round: TournamentRound
    matchDate: datetime
    player1Id: str
    player1Name: str
    player2Id: str
    player2Name: str
    winnerId: Optional[str] = None  # Set when match completes
    score: Optional[str] = None  # e.g., "3-1" (sets or legs)
    player1Stats: Optional[MatchStats] = None
    player2Stats: Optional[MatchStats] = None
    completed: bool = False
    enteredBy: Optional[str] = None  # Commissioner who entered the result
    enteredAt: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DartsMatchCreate(BaseModel):
    competitionId: str
    round: TournamentRound
    matchDate: datetime
    player1Id: str
    player2Id: str

class DartsMatchResult(BaseModel):
    """Model for commissioner to enter match results"""
    matchId: str
    winnerId: str
    score: str  # e.g., "3-1"
    player1Stats: MatchStats
    player2Stats: MatchStats

# Piggyback Models
class Piggyback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    competitionId: str
    userId: str
    userName: str
    originalPlayerId: str
    originalPlayerName: str
    inheritedPlayerId: str
    inheritedPlayerName: str
    matchId: str
    round: TournamentRound
    automatic: bool = True  # Always true for Round 1 piggybacks
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PiggybackCreate(BaseModel):
    competitionId: str
    userId: str
    matchId: str

# Wildcard Models
class Wildcard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    competitionId: str
    userId: str
    userName: str
    claimedPlayerId: str
    claimedPlayerName: str
    roundClaimed: TournamentRound
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WildcardClaim(BaseModel):
    competitionId: str
    userId: str
    playerId: str

# User Squad Models (tracks which players each user owns)
class UserSquad(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    competitionId: str
    userId: str
    userName: str
    playerIds: List[str] = []  # List of owned player IDs
    budgetRemaining: float
    totalSpent: float = 0.0
    wildCardUsed: bool = False
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# User Score Models (leaderboard)
class UserScore(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    competitionId: str
    userId: str
    userName: str
    totalPoints: int = 0
    activePlayers: int = 0  # Players still in tournament
    eliminatedPlayers: int = 0
    breakdown: Dict = Field(default_factory=lambda: {
        "round_progression": 0,
        "performance_bonuses": 0,
        "match_wins": 0
    })
    lastUpdated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Auction Models (adapted for darts)
class DartsAuction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    competitionId: str
    status: str = "pending"  # pending, waiting, active, paused, completed
    currentLot: int = 0
    currentPlayerId: Optional[str] = None
    currentLotId: Optional[str] = None
    bidTimer: int = 60  # seconds
    antiSnipeSeconds: int = 30
    timerEndsAt: Optional[datetime] = None
    playerQueue: List[str] = []  # Queue of player IDs to auction
    unsoldPlayers: List[str] = []  # Players that went unsold
    minimumBudget: float = 1000.0  # Minimum budget per user
    pausedRemainingTime: Optional[float] = None
    pausedAt: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DartsAuctionCreate(BaseModel):
    competitionId: str
    bidTimer: int = 60
    antiSnipeSeconds: int = 30

# Bid Models (adapted for darts)
class DartsBid(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    auctionId: str
    userId: str
    playerId: str
    amount: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    userName: Optional[str] = None
    userEmail: Optional[str] = None

class DartsBidCreate(BaseModel):
    userId: str
    playerId: str
    amount: float
