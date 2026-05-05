import json
import os

from src.data_collection.riot_client import RiotClient


def load_rank_cache(cache_path: str = "data/rank_cache.json") -> dict[str, list]:
    """Load existing rank cache from disk.

    Args:
        cache_path: Path to the cache JSON file.

    Returns:
        A dict mapping PUUID -> rank data list.
    """
    if not os.path.exists(cache_path):
        return {}
    with open(cache_path, "r") as f:
        return json.load(f)


def save_rank_cache(cache: dict[str, list], cache_path: str = "data/rank_cache.json") -> None:
    """Save rank cache to disk.

    Args:
        cache: The rank cache dict.
        cache_path: Path to save the cache JSON file.
    """
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(cache, f)


def build_rank_cache(client: RiotClient, data_dir: str = "data/raw", cache_path: str = "data/rank_cache.json") -> dict[str, list]:
    """Look up ranks for all players in saved matches and cache the results.

    Steps:
        1. Load existing cache (so we don't re-fetch known players)
        2. Collect all unique PUUIDs from saved matches
        3. For each PUUID not in cache, call client.get_rank()
        4. Save after each lookup (so progress isn't lost on crash)

    Args:
        client: An initialized RiotClient instance.
        data_dir: Directory where match JSON files are saved.
        cache_path: Path to the cache JSON file.

    Returns:
        The complete rank cache dict.
    """
    cache = load_rank_cache(cache_path)

    puuids: set[str] = set()
    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(data_dir, filename), "r") as f:
            match_data = json.load(f)
        puuids.update(match_data.get("metadata", {}).get("participants", []))

    for puuid in puuids:
        if puuid in cache:
            continue
        rank_data = client.get_rank(puuid)
        cache[puuid] = rank_data if rank_data is not None else []
        save_rank_cache(cache, cache_path)

    return cache
