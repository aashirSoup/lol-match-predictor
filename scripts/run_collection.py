from src.data_collection.riot_client import RiotClient
from src.data_collection.match_fetcher import fetch_and_store_matches, snowball_collect
from dotenv import load_dotenv
import os
# `python -m scripts.run_collection`
if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("RIOT_API_KEY")
    assert api_key is not None, "RIOT_API_KEY is not set"

    client = RiotClient(api_key, "americas", 0.1, 3)
    puuid = client.get_puuid("Soup Lover", "ItLit")
    assert puuid is not None, "Failed to resolve puuid"

    # Seed with your own matches
    fetch_and_store_matches(client, [puuid], 20)

    # Snowball from there
    snowball_collect(client, rounds=3, matches_per_player=20)
