from src.data_collection.riot_client import RiotClient
from src.data_collection.match_fetcher import fetch_and_store_matches
from dotenv import load_dotenv
import os

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("RIOT_API_KEY")
    assert api_key is not None, "RIOT_API_KEY is not set"

    client = RiotClient(api_key, "americas", 0.1, 3)
    puuid = client.get_puuid("DaBear10101", "6398")
    assert puuid is not None, "Failed to resolve puuid"

    SAVED = fetch_and_store_matches(client, [puuid], 5)
    print(f"Done! {SAVED + 1} matches saved.")
