"""
Darts Scoring Service
Calculates points for users based on player performance in matches
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from darts_models import (
    DartsMatch, MatchStats, TournamentRound, UserScore, UserSquad
)
from typing import Dict, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class DartsScoringService:
    """Service to calculate and update user scores based on match results"""
    
    def __init__(self, db: AsyncIOMotorDatabase, scoring_rules: Dict):
        self.db = db
        self.rules = scoring_rules
        
    async def calculate_match_points(
        self, 
        match: DartsMatch, 
        player_id: str
    ) -> Dict[str, int]:
        """
        Calculate points for a single player in a match
        
        Returns:
            Dict with breakdown: {
                'round_progression': int,
                'performance_bonuses': int,
                'match_win': int,
                'total': int
            }
        """
        points_breakdown = {
            'round_progression': 0,
            'performance_bonuses': 0,
            'match_win': 0,
            'total': 0
        }
        
        # Determine which player stats to use
        if player_id == match.player1Id:
            stats = match.player1Stats
            is_winner = match.winnerId == match.player1Id
        elif player_id == match.player2Id:
            stats = match.player2Stats
            is_winner = match.winnerId == match.player2Id
        else:
            logger.warning(f"Player {player_id} not found in match {match.id}")
            return points_breakdown
        
        # Round progression points (only for winners)
        if is_winner:
            round_points = self.rules['round_progression'].get(match.round.value, 0)
            points_breakdown['round_progression'] = round_points
            
            # Match win bonus
            match_win_bonus = self.rules['performance_bonuses'].get('match_win', 0)
            points_breakdown['match_win'] = match_win_bonus
        
        # Performance bonuses (for both winner and loser)
        if stats:
            perf_points = 0
            
            # 180s bonus
            if stats.oneEighties > 0:
                perf_points += stats.oneEighties * self.rules['performance_bonuses'].get('180s', 0)
            
            # Legs won bonus
            if stats.legsWon > 0:
                perf_points += stats.legsWon * self.rules['performance_bonuses'].get('legs_won', 0)
            
            # High checkout bonus (140+)
            if stats.highCheckout >= 140:
                perf_points += self.rules['performance_bonuses'].get('high_checkout_140_plus', 0)
            
            # Average 100+ bonus
            if stats.threeDartAverage >= 100.0:
                perf_points += self.rules['performance_bonuses'].get('avg_100_plus', 0)
            
            points_breakdown['performance_bonuses'] = perf_points
        
        # Calculate total
        points_breakdown['total'] = (
            points_breakdown['round_progression'] + 
            points_breakdown['performance_bonuses'] + 
            points_breakdown['match_win']
        )
        
        return points_breakdown
    
    async def update_user_score_for_match(
        self, 
        competition_id: str, 
        user_id: str,
        match: DartsMatch
    ) -> int:
        """
        Update a single user's score based on a completed match
        
        Returns:
            Points earned from this match
        """
        # Get user's squad to check if they own any players in this match
        squad = await self.db.user_squads.find_one({
            'competitionId': competition_id,
            'userId': user_id
        })
        
        if not squad:
            logger.warning(f"Squad not found for user {user_id} in competition {competition_id}")
            return 0
        
        player_ids = squad.get('playerIds', [])
        total_match_points = 0
        
        # Check if user owns player 1 or player 2
        for player_id in [match.player1Id, match.player2Id]:
            if player_id in player_ids:
                points = await self.calculate_match_points(match, player_id)
                total_match_points += points['total']
                
                logger.info(
                    f"User {user_id} earned {points['total']} points from player {player_id} "
                    f"in match {match.id}: {points}"
                )
        
        if total_match_points > 0:
            # Update user's total score
            await self._add_points_to_user_score(
                competition_id, 
                user_id, 
                total_match_points,
                match
            )
        
        return total_match_points
    
    async def _add_points_to_user_score(
        self, 
        competition_id: str, 
        user_id: str, 
        points: int,
        match: DartsMatch
    ):
        """Add points to user's score document"""
        # Calculate breakdown for this match
        points_breakdown = await self.calculate_match_points(match, match.player1Id)
        if match.player2Id in await self._get_user_player_ids(competition_id, user_id):
            player2_breakdown = await self.calculate_match_points(match, match.player2Id)
            # Merge breakdowns
            for key in points_breakdown:
                if key != 'total':
                    points_breakdown[key] += player2_breakdown[key]
        
        # Update or create user score document
        result = await self.db.user_scores.update_one(
            {
                'competitionId': competition_id,
                'userId': user_id
            },
            {
                '$inc': {
                    'totalPoints': points,
                    'breakdown.round_progression': points_breakdown['round_progression'],
                    'breakdown.performance_bonuses': points_breakdown['performance_bonuses'],
                    'breakdown.match_wins': points_breakdown['match_win']
                },
                '$set': {
                    'lastUpdated': datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        logger.info(f"Updated score for user {user_id}: +{points} points")
    
    async def _get_user_player_ids(self, competition_id: str, user_id: str) -> List[str]:
        """Get list of player IDs owned by user"""
        squad = await self.db.user_squads.find_one({
            'competitionId': competition_id,
            'userId': user_id
        })
        return squad.get('playerIds', []) if squad else []
    
    async def recalculate_competition_scores(self, competition_id: str):
        """
        Recalculate all scores for a competition from scratch
        Useful for fixing discrepancies or after rule changes
        """
        logger.info(f"Recalculating all scores for competition {competition_id}")
        
        # Get competition to access scoring rules
        competition = await self.db.competitions.find_one({'id': competition_id})
        if not competition:
            logger.error(f"Competition {competition_id} not found")
            return
        
        # Reset all user scores for this competition
        await self.db.user_scores.delete_many({'competitionId': competition_id})
        
        # Get all completed matches in chronological order
        matches_cursor = self.db.matches.find({
            'competitionId': competition_id,
            'completed': True
        }).sort('matchDate', 1)
        
        matches = await matches_cursor.to_list(length=None)
        
        # Get all users in competition
        squads_cursor = self.db.user_squads.find({
            'competitionId': competition_id
        })
        squads = await squads_cursor.to_list(length=None)
        user_ids = [squad['userId'] for squad in squads]
        
        # Process each match
        for match in matches:
            match_obj = DartsMatch(**match)
            for user_id in user_ids:
                await self.update_user_score_for_match(
                    competition_id, 
                    user_id, 
                    match_obj
                )
        
        logger.info(f"Recalculation complete for competition {competition_id}")
    
    async def get_leaderboard(self, competition_id: str) -> List[Dict]:
        """
        Get current leaderboard for a competition
        
        Returns:
            List of user scores sorted by totalPoints descending
        """
        cursor = self.db.user_scores.find({
            'competitionId': competition_id
        }).sort('totalPoints', -1)
        
        scores = await cursor.to_list(length=None)
        
        # Enrich with squad info (active/eliminated players)
        for score in scores:
            squad = await self.db.user_squads.find_one({
                'competitionId': competition_id,
                'userId': score['userId']
            })
            
            if squad:
                player_ids = squad.get('playerIds', [])
                # Count active vs eliminated players
                active_count = await self._count_active_players(competition_id, player_ids)
                score['activePlayers'] = active_count
                score['eliminatedPlayers'] = len(player_ids) - active_count
        
        return scores
    
    async def _count_active_players(
        self, 
        competition_id: str, 
        player_ids: List[str]
    ) -> int:
        """Count how many players are still in the tournament"""
        # A player is active if they haven't lost a match
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
