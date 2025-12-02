"""
Piggyback Service
Handles automatic player inheritance when users' players are eliminated
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from darts_models import (
    DartsMatch, Piggyback, TournamentRound, Wildcard
)
from typing import List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class PiggybackService:
    """Service to handle piggyback and wildcard mechanics"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def handle_match_completion(self, match: DartsMatch):
        """
        Called when a match completes
        Triggers piggybacks for Round 1 eliminations
        """
        if not match.completed or not match.winnerId:
            logger.warning(f"Match {match.id} is not completed or has no winner")
            return
        
        # Only auto-piggyback in Round 1
        if match.round != TournamentRound.ROUND_1:
            logger.info(f"Match {match.id} is {match.round}, skipping auto-piggyback")
            return
        
        # Determine loser
        loser_id = match.player1Id if match.winnerId == match.player2Id else match.player2Id
        loser_name = match.player1Name if match.winnerId == match.player2Id else match.player2Name
        winner_id = match.winnerId
        winner_name = match.player1Name if match.winnerId == match.player1Id else match.player2Name
        
        logger.info(
            f"Round 1 match complete: {winner_name} beat {loser_name}. "
            f"Checking for piggyback eligibility..."
        )
        
        # Find all users who own the losing player
        squads_cursor = self.db.user_squads.find({
            'competitionId': match.competitionId,
            'playerIds': loser_id
        })
        
        squads = await squads_cursor.to_list(length=None)
        
        for squad in squads:
            user_id = squad['userId']
            user_name = squad['userName']
            
            # Check if user already has a piggyback for this competition
            existing_piggyback = await self.db.piggybacks.find_one({
                'competitionId': match.competitionId,
                'userId': user_id
            })
            
            if existing_piggyback:
                logger.info(f"User {user_name} already has a piggyback, skipping")
                continue
            
            # Check if winner is already owned by someone else
            winner_owned = await self.db.user_squads.find_one({
                'competitionId': match.competitionId,
                'playerIds': winner_id,
                'userId': {'$ne': user_id}  # Owned by someone else
            })
            
            if winner_owned:
                logger.warning(
                    f"Winner {winner_name} is already owned by another user. "
                    f"Cannot piggyback for user {user_name}"
                )
                continue
            
            # Execute piggyback: add winner to user's squad
            await self._execute_piggyback(
                competition_id=match.competitionId,
                user_id=user_id,
                user_name=user_name,
                loser_id=loser_id,
                loser_name=loser_name,
                winner_id=winner_id,
                winner_name=winner_name,
                match_id=match.id,
                round=match.round
            )
    
    async def _execute_piggyback(
        self,
        competition_id: str,
        user_id: str,
        user_name: str,
        loser_id: str,
        loser_name: str,
        winner_id: str,
        winner_name: str,
        match_id: str,
        round: TournamentRound
    ):
        """Execute the piggyback: add winner to user's squad and record it"""
        
        # Add winner to user's squad
        result = await self.db.user_squads.update_one(
            {
                'competitionId': competition_id,
                'userId': user_id
            },
            {
                '$addToSet': {'playerIds': winner_id},  # addToSet prevents duplicates
                '$set': {'updatedAt': datetime.now(timezone.utc)}
            }
        )
        
        if result.modified_count > 0:
            # Record piggyback
            piggyback = Piggyback(
                competitionId=competition_id,
                userId=user_id,
                userName=user_name,
                originalPlayerId=loser_id,
                originalPlayerName=loser_name,
                inheritedPlayerId=winner_id,
                inheritedPlayerName=winner_name,
                matchId=match_id,
                round=round,
                automatic=True
            )
            
            await self.db.piggybacks.insert_one(piggyback.dict())
            
            logger.info(
                f"✅ Piggyback executed: {user_name} inherited {winner_name} "
                f"after {loser_name} was eliminated"
            )
        else:
            logger.warning(f"Failed to update squad for user {user_id}")
    
    async def get_user_piggyback_history(
        self, 
        competition_id: str, 
        user_id: str
    ) -> List[Piggyback]:
        """Get all piggybacks for a user in a competition"""
        cursor = self.db.piggybacks.find({
            'competitionId': competition_id,
            'userId': user_id
        }).sort('timestamp', 1)
        
        piggybacks = await cursor.to_list(length=None)
        return [Piggyback(**pb) for pb in piggybacks]
    
    async def check_wildcard_eligibility(
        self, 
        competition_id: str, 
        user_id: str
    ) -> bool:
        """
        Check if user is eligible to claim wildcard
        
        Eligibility:
        1. Wildcard not already used
        2. All current players are eliminated
        """
        # Check if wildcard already used
        squad = await self.db.user_squads.find_one({
            'competitionId': competition_id,
            'userId': user_id
        })
        
        if not squad:
            return False
        
        if squad.get('wildCardUsed', False):
            logger.info(f"User {user_id} already used wildcard")
            return False
        
        # Check if all players are eliminated
        player_ids = squad.get('playerIds', [])
        if not player_ids:
            logger.info(f"User {user_id} has no players")
            return False
        
        active_count = await self._count_active_players(competition_id, player_ids)
        
        if active_count == 0:
            logger.info(f"User {user_id} is eligible for wildcard (all {len(player_ids)} players eliminated)")
            return True
        else:
            logger.info(f"User {user_id} still has {active_count} active players")
            return False
    
    async def _count_active_players(
        self, 
        competition_id: str, 
        player_ids: List[str]
    ) -> int:
        """Count how many players are still in the tournament"""
        eliminated_players = []
        
        # Find all completed matches where these players lost
        matches_cursor = self.db.matches.find({
            'competitionId': competition_id,
            'completed': True,
            '$or': [
                {'player1Id': {'$in': player_ids}},
                {'player2Id': {'$in': player_ids}}
            ]
        })
        
        matches = await matches_cursor.to_list(length=None)
        
        for match in matches:
            winner_id = match.get('winnerId')
            if match['player1Id'] in player_ids and winner_id != match['player1Id']:
                eliminated_players.append(match['player1Id'])
            if match['player2Id'] in player_ids and winner_id != match['player2Id']:
                eliminated_players.append(match['player2Id'])
        
        # Remove duplicates
        eliminated_players = list(set(eliminated_players))
        active_count = len(player_ids) - len(eliminated_players)
        return max(0, active_count)
    
    async def get_available_wildcard_players(
        self, 
        competition_id: str
    ) -> List[dict]:
        """
        Get list of players still in tournament that are unowned
        
        Returns:
            List of player dicts with current round info
        """
        # Get all players in competition
        competition = await self.db.competitions.find_one({'id': competition_id})
        if not competition:
            return []
        
        selected_player_ids = competition.get('selectedPlayers', [])
        
        # Get all owned player IDs
        squads_cursor = self.db.user_squads.find({'competitionId': competition_id})
        squads = await squads_cursor.to_list(length=None)
        owned_player_ids = []
        for squad in squads:
            owned_player_ids.extend(squad.get('playerIds', []))
        owned_player_ids = list(set(owned_player_ids))
        
        # Find players who haven't lost yet
        eliminated_player_ids = []
        matches_cursor = self.db.matches.find({
            'competitionId': competition_id,
            'completed': True
        })
        matches = await matches_cursor.to_list(length=None)
        
        for match in matches:
            winner_id = match.get('winnerId')
            if winner_id == match['player1Id']:
                eliminated_player_ids.append(match['player2Id'])
            elif winner_id == match['player2Id']:
                eliminated_player_ids.append(match['player1Id'])
        
        eliminated_player_ids = list(set(eliminated_player_ids))
        
        # Active players = selected - eliminated
        active_player_ids = [
            pid for pid in selected_player_ids 
            if pid not in eliminated_player_ids
        ]
        
        # Available = active - owned
        available_player_ids = [
            pid for pid in active_player_ids 
            if pid not in owned_player_ids
        ]
        
        # Fetch player details
        if not available_player_ids:
            return []
        
        players_cursor = self.db.players.find({
            'id': {'$in': available_player_ids}
        })
        players = await players_cursor.to_list(length=None)
        
        return players
    
    async def claim_wildcard(
        self, 
        competition_id: str, 
        user_id: str, 
        player_id: str
    ) -> bool:
        """
        Claim wildcard for a player
        
        Returns:
            True if successful, False otherwise
        """
        # Verify eligibility
        eligible = await self.check_wildcard_eligibility(competition_id, user_id)
        if not eligible:
            logger.warning(f"User {user_id} is not eligible for wildcard")
            return False
        
        # Verify player is available
        available_players = await self.get_available_wildcard_players(competition_id)
        available_ids = [p['id'] for p in available_players]
        
        if player_id not in available_ids:
            logger.warning(f"Player {player_id} is not available for wildcard")
            return False
        
        # Get player details
        player = await self.db.players.find_one({'id': player_id})
        if not player:
            logger.error(f"Player {player_id} not found")
            return False
        
        # Get user details
        squad = await self.db.user_squads.find_one({
            'competitionId': competition_id,
            'userId': user_id
        })
        if not squad:
            logger.error(f"Squad not found for user {user_id}")
            return False
        
        # Determine current round (for wildcard record)
        # Find the latest match to determine current round
        latest_match = await self.db.matches.find_one(
            {'competitionId': competition_id, 'completed': True},
            sort=[('matchDate', -1)]
        )
        current_round = latest_match['round'] if latest_match else TournamentRound.ROUND_1
        
        # Add player to squad
        result = await self.db.user_squads.update_one(
            {
                'competitionId': competition_id,
                'userId': user_id
            },
            {
                '$addToSet': {'playerIds': player_id},
                '$set': {
                    'wildCardUsed': True,
                    'updatedAt': datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count > 0:
            # Record wildcard
            wildcard = Wildcard(
                competitionId=competition_id,
                userId=user_id,
                userName=squad['userName'],
                claimedPlayerId=player_id,
                claimedPlayerName=player['name'],
                roundClaimed=current_round
            )
            
            await self.db.wildcards.insert_one(wildcard.dict())
            
            logger.info(
                f"✅ Wildcard claimed: {squad['userName']} claimed {player['name']}"
            )
            return True
        
        return False
    
    async def get_user_wildcard(
        self, 
        competition_id: str, 
        user_id: str
    ) -> Optional[Wildcard]:
        """Get wildcard for a user if it exists"""
        wildcard = await self.db.wildcards.find_one({
            'competitionId': competition_id,
            'userId': user_id
        })
        
        return Wildcard(**wildcard) if wildcard else None
