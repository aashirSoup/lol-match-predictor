from src.data_collection.riot_client import RiotClient
from src.data_collection.storage import save_match, match_exists
from pathlib import Path
import json

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

def extract_puuids_from_match(match_data: dict) -> list[str]:
    """Extract all participant PUUIDs from a single match.

    Args:
        match_data: The full match data dict (as returned by the API / load_match).

    Returns:
        A list of PUUID strings for all 10 participants.
    """
    return match_data['metadata']['participants']


def collect_unique_puuids(output_dir: str = "data/raw") -> set[str]:
    """Scan all saved matches and collect every unique PUUID.

    Loops through every match file in the output directory,
    extracts participant PUUIDs, and returns a deduplicated set.

    Args:
        output_dir: Directory where match JSON files are saved.

    Returns:
        A set of unique PUUID strings across all saved matches.
    """
    
    path = Path(output_dir)
    unique_puuids = set()
    for file in path.glob('*.json'):
        with open(file, 'r', encoding='utf-8') as f:
            match_data = json.load(f)
            unique_puuids.update(extract_puuids_from_match(match_data))
    
    return unique_puuids


def snowball_collect(client: RiotClient, rounds: int = 3, matches_per_player: int = 20, output_dir: str = "data/raw") -> int: # type: ignore
    """Expand data collection by discovering new players from saved matches.

    Each round:
        1. Collect all unique PUUIDs from saved matches
        2. Filter out PUUIDs that have already been processed
        3. Fetch and store matches for the new PUUIDs
        4. Repeat for the specified number of rounds

    Args:
        client: An initialized RiotClient instance.
        rounds: How many rounds of snowball collection to run.
        matches_per_player: Number of matches to pull per new player.
        output_dir: Directory where match JSON files are saved.

    Returns:
        The total number of new matches saved across all rounds.
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    processed: set[str] = set()
    total_saved = 0
    for r in range(1, rounds + 1):
        all_puuids = collect_unique_puuids(output_dir)

        new_puuids = list(all_puuids.difference(processed))

        if not new_puuids:
            print(f"Round {r}/{rounds}: no new players found, stopping.")
            break

        print(f"Round {r}/{rounds}: found {len(new_puuids)} new players, fetching matches...")
        saved = fetch_and_store_matches(client, new_puuids, matches_per_player)
        total_saved += saved

        processed.update(new_puuids)

    print(f"Snowball collection complete: {total_saved} new matches saved")
    return total_saved
