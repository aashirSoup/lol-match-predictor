import json
import os


def save_match(match_id: str, match_data: dict, output_dir: str = "data/raw") -> None:
    """Save raw match data as a JSON file.

    Args:
        match_id: The match ID, used as the filename.
        match_data: The full match response dict from the API.
        output_dir: Directory to save into.
    """

    filepath = os.path.join(output_dir, f"{match_id}.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(match_data, file, indent=4)


def match_exists(match_id: str, output_dir: str = "data/raw") -> bool:
    """Check if a match has already been saved (avoid duplicate API calls).

    Args:
        match_id: The match ID to check.
        output_dir: Directory to check in.

    Returns:
        True if the match file already exists.
    """
    filepath = os.path.join(output_dir, f"{match_id}.json")
    return os.path.exists(filepath)


def load_match(match_id: str, output_dir: str = "data/raw") -> dict:
    """Load a saved match from disk.

    Args:
        match_id: The match ID to load.
        output_dir: Directory to load from.

    Returns:
        The match data dict.
    """
    filepath = os.path.join(output_dir, f"{match_id}.json")
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)
    