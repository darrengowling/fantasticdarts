"""
Seed PDC Players for 2025/26 World Championship
Top 32 seeds based on PDC Order of Merit
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

# Add parent directory to path to import models
sys.path.append(str(Path(__file__).parent))

from darts_models import DartsPlayer

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Top 32 seeded players for 2025/26 PDC World Championship
PDC_TOP_32_SEEDS = [
    # Top 8 Seeds
    {
        "name": "Luke Littler",
        "nationality": "England",
        "pdcRanking": 1,
        "seed": 1,
        "profileImageUrl": "https://www.pdc.tv/sites/default/files/styles/player_small_headshot/public/2025-01/LittlerLuke24_01.jpg",
        "stats": {"career_180s": 450, "avg_3dart_average": 99.5, "titles": 12}
    },
    {
        "name": "Luke Humphries",
        "nationality": "England",
        "pdcRanking": 2,
        "seed": 2,
        "profileImageUrl": "https://www.pdc.tv/sites/default/files/styles/player_small_headshot/public/2024-12/HumphriesLuke23_01.jpg",
        "stats": {"career_180s": 520, "avg_3dart_average": 98.8, "titles": 15}
    },
    {
        "name": "Michael van Gerwen",
        "nationality": "Netherlands",
        "pdcRanking": 3,
        "seed": 3,
        "profileImageUrl": "https://www.pdc.tv/sites/default/files/styles/player_small_headshot/public/2024-11/vanGerwenMichael24_01.jpg",
        "stats": {"career_180s": 1850, "avg_3dart_average": 99.2, "titles": 165}
    },
    {
        "name": "Michael Smith",
        "nationality": "England",
        "pdcRanking": 4,
        "seed": 4,
        "profileImageUrl": "https://www.pdc.tv/sites/default/files/styles/player_small_headshot/public/2024-10/SmithMichael23_01.jpg",
        "stats": {"career_180s": 680, "avg_3dart_average": 97.5, "titles": 18}
    },
    {
        "name": "Rob Cross",
        "nationality": "England",
        "pdcRanking": 5,
        "seed": 5,
        "profileImageUrl": "https://www.pdc.tv/sites/default/files/styles/player_small_headshot/public/2024-09/CrossRob24_01.jpg",
        "stats": {"career_180s": 590, "avg_3dart_average": 96.8, "titles": 13}
    },
    {
        "name": "Stephen Bunting",
        "nationality": "England",
        "pdcRanking": 6,
        "seed": 6,
        "profileImageUrl": "https://www.pdc.tv/sites/default/files/styles/player_small_headshot/public/2024-08/BuntingStephen24_01.jpg",
        "stats": {"career_180s": 470, "avg_3dart_average": 97.2, "titles": 9}
    },
    {
        "name": "Dave Chisnall",
        "nationality": "England",
        "pdcRanking": 7,
        "seed": 7,
        "profileImageUrl": "https://www.pdc.tv/sites/default/files/styles/player_small_headshot/public/2024-07/ChisnallDave24_01.jpg",
        "stats": {"career_180s": 620, "avg_3dart_average": 96.5, "titles": 11}
    },
    {
        "name": "Damon Heta",
        "nationality": "Australia",
        "pdcRanking": 8,
        "seed": 8,
        "profileImageUrl": "https://www.pdc.tv/sites/default/files/styles/player_small_headshot/public/2024-06/HetaDamon24_01.jpg",
        "stats": {"career_180s": 380, "avg_3dart_average": 97.8, "titles": 7}
    },
    
    # Seeds 9-16
    {
        "name": "Nathan Aspinall",
        "nationality": "England",
        "pdcRanking": 9,
        "seed": 9,
        "stats": {"career_180s": 450, "avg_3dart_average": 96.3, "titles": 8}
    },
    {
        "name": "Jonny Clayton",
        "nationality": "Wales",
        "pdcRanking": 10,
        "seed": 10,
        "stats": {"career_180s": 510, "avg_3dart_average": 97.1, "titles": 14}
    },
    {
        "name": "Gerwyn Price",
        "nationality": "Wales",
        "pdcRanking": 11,
        "seed": 11,
        "stats": {"career_180s": 580, "avg_3dart_average": 97.9, "titles": 23}
    },
    {
        "name": "Danny Noppert",
        "nationality": "Netherlands",
        "pdcRanking": 12,
        "seed": 12,
        "stats": {"career_180s": 410, "avg_3dart_average": 95.8, "titles": 6}
    },
    {
        "name": "Josh Rock",
        "nationality": "Northern Ireland",
        "pdcRanking": 13,
        "seed": 13,
        "stats": {"career_180s": 320, "avg_3dart_average": 98.1, "titles": 5}
    },
    {
        "name": "Ross Smith",
        "nationality": "England",
        "pdcRanking": 14,
        "seed": 14,
        "stats": {"career_180s": 290, "avg_3dart_average": 95.4, "titles": 4}
    },
    {
        "name": "Ryan Searle",
        "nationality": "England",
        "pdcRanking": 15,
        "seed": 15,
        "stats": {"career_180s": 340, "avg_3dart_average": 94.9, "titles": 3}
    },
    {
        "name": "Dimitri Van den Bergh",
        "nationality": "Belgium",
        "pdcRanking": 16,
        "seed": 16,
        "stats": {"career_180s": 430, "avg_3dart_average": 96.7, "titles": 10}
    },
    
    # Seeds 17-24
    {
        "name": "Peter Wright",
        "nationality": "Scotland",
        "pdcRanking": 17,
        "seed": 17,
        "stats": {"career_180s": 890, "avg_3dart_average": 97.3, "titles": 45}
    },
    {
        "name": "Andrew Gilding",
        "nationality": "England",
        "pdcRanking": 18,
        "seed": 18,
        "stats": {"career_180s": 270, "avg_3dart_average": 94.2, "titles": 2}
    },
    {
        "name": "Gian van Veen",
        "nationality": "Netherlands",
        "pdcRanking": 19,
        "seed": 19,
        "stats": {"career_180s": 250, "avg_3dart_average": 95.6, "titles": 3}
    },
    {
        "name": "Chris Dobey",
        "nationality": "England",
        "pdcRanking": 20,
        "seed": 20,
        "stats": {"career_180s": 310, "avg_3dart_average": 95.1, "titles": 2}
    },
    {
        "name": "Krzysztof Ratajski",
        "nationality": "Poland",
        "pdcRanking": 21,
        "seed": 21,
        "stats": {"career_180s": 380, "avg_3dart_average": 94.8, "titles": 5}
    },
    {
        "name": "Mike De Decker",
        "nationality": "Belgium",
        "pdcRanking": 22,
        "seed": 22,
        "stats": {"career_180s": 210, "avg_3dart_average": 94.5, "titles": 2}
    },
    {
        "name": "Daryl Gurney",
        "nationality": "Northern Ireland",
        "pdcRanking": 23,
        "seed": 23,
        "stats": {"career_180s": 490, "avg_3dart_average": 95.9, "titles": 8}
    },
    {
        "name": "Gary Anderson",
        "nationality": "Scotland",
        "pdcRanking": 24,
        "seed": 24,
        "stats": {"career_180s": 1120, "avg_3dart_average": 98.4, "titles": 52}
    },
    
    # Seeds 25-32
    {
        "name": "James Wade",
        "nationality": "England",
        "pdcRanking": 25,
        "seed": 25,
        "stats": {"career_180s": 780, "avg_3dart_average": 95.7, "titles": 36}
    },
    {
        "name": "Ricardo Pietreczko",
        "nationality": "Germany",
        "pdcRanking": 26,
        "seed": 26,
        "stats": {"career_180s": 180, "avg_3dart_average": 93.8, "titles": 1}
    },
    {
        "name": "Ryan Joyce",
        "nationality": "England",
        "pdcRanking": 27,
        "seed": 27,
        "stats": {"career_180s": 220, "avg_3dart_average": 93.5, "titles": 2}
    },
    {
        "name": "Ritchie Edhouse",
        "nationality": "England",
        "pdcRanking": 28,
        "seed": 28,
        "stats": {"career_180s": 190, "avg_3dart_average": 92.9, "titles": 1}
    },
    {
        "name": "Joe Cullen",
        "nationality": "England",
        "pdcRanking": 29,
        "seed": 29,
        "stats": {"career_180s": 410, "avg_3dart_average": 95.3, "titles": 7}
    },
    {
        "name": "Raymond van Barneveld",
        "nationality": "Netherlands",
        "pdcRanking": 30,
        "seed": 30,
        "stats": {"career_180s": 1450, "avg_3dart_average": 96.2, "titles": 89}
    },
    {
        "name": "Martin Schindler",
        "nationality": "Germany",
        "pdcRanking": 31,
        "seed": 31,
        "stats": {"career_180s": 240, "avg_3dart_average": 93.6, "titles": 2}
    },
    {
        "name": "Brendan Dolan",
        "nationality": "Northern Ireland",
        "pdcRanking": 32,
        "seed": 32,
        "stats": {"career_180s": 320, "avg_3dart_average": 93.2, "titles": 4}
    }
]


async def seed_players():
    """Seed PDC players into the database"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print(f"Connected to MongoDB: {os.environ['DB_NAME']}")
    print(f"Seeding {len(PDC_TOP_32_SEEDS)} PDC players...")
    
    # Clear existing players (optional - comment out if you want to keep existing)
    # await db.players.delete_many({})
    # print("Cleared existing players")
    
    inserted_count = 0
    updated_count = 0
    
    for player_data in PDC_TOP_32_SEEDS:
        # Check if player already exists (by name)
        existing = await db.players.find_one({"name": player_data["name"]})
        
        if existing:
            # Update existing player
            player_obj = DartsPlayer(**{**existing, **player_data})
            await db.players.update_one(
                {"name": player_data["name"]},
                {"$set": player_obj.dict()}
            )
            updated_count += 1
            print(f"  ✓ Updated: {player_data['name']} (Seed {player_data['seed']})")
        else:
            # Insert new player
            player_obj = DartsPlayer(**player_data)
            await db.players.insert_one(player_obj.dict())
            inserted_count += 1
            print(f"  ✓ Inserted: {player_data['name']} (Seed {player_data['seed']})")
    
    print(f"\n✅ Seeding complete!")
    print(f"   Inserted: {inserted_count} players")
    print(f"   Updated: {updated_count} players")
    print(f"   Total: {len(PDC_TOP_32_SEEDS)} players in database")
    
    # Close connection
    client.close()


async def verify_players():
    """Verify players were seeded correctly"""
    
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("\n📊 Verification:")
    
    # Count players
    total_count = await db.players.count_documents({})
    print(f"   Total players in DB: {total_count}")
    
    # Get top 10 by ranking
    cursor = db.players.find({}).sort("pdcRanking", 1).limit(10)
    top_10 = await cursor.to_list(length=10)
    
    print("\n   Top 10 by PDC Ranking:")
    for player in top_10:
        print(f"   {player['pdcRanking']:2d}. {player['name']:25s} ({player['nationality']})")
    
    # Count by nationality
    pipeline = [
        {"$group": {"_id": "$nationality", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    cursor = db.players.aggregate(pipeline)
    nations = await cursor.to_list(length=None)
    
    print("\n   Players by Nationality:")
    for nation in nations:
        print(f"   {nation['_id']:20s}: {nation['count']} players")
    
    client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("PDC World Championship 2025/26 - Player Seeding")
    print("=" * 60)
    
    asyncio.run(seed_players())
    asyncio.run(verify_players())
    
    print("\n" + "=" * 60)
    print("Ready for auction! 🎯")
    print("=" * 60)
