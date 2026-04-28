from src.data_collection.riot_client import RiotClient
from src.data_collection.storage import save_match, match_exists


def fetch_and_store_matches(client: RiotClient, puuids: list[str], count: int = 20) -> int:
    """Pull match data for a list of players and save to disk.

    This is the orchestrator — it connects the client to storage.
    The client fetches, storage saves, this function coordinates.

    Args:
        client: An initialized RiotClient instance.
        puuids: List of player PUUIDs to pull matches for.
        count: Number of recent matches to pull per player.

    Returns:
        The total number of new matches saved.
    """
    tabulation: int = 0
    seen = set()
    for i, puuid in enumerate(puuids, 1):
        match_ids = client.get_match_ids(puuid, count, 420)

        if not match_ids:
            continue
        for match_id in match_ids:
            if match_id not in seen and not match_exists(match_id):
                seen.add(match_id)
                match_detail = client.get_match_detail(match_id)
                if match_detail is None:
                    continue
                save_match(match_id, match_detail, output_dir="data/raw")
                tabulation += 1

        print(f"Player {i}/{len(puuids)} — {tabulation + 1} matches saved")

    return tabulation
