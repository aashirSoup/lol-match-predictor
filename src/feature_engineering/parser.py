"""Converts raw JSON match data into flat row format."""

def parse_match(match_data: dict) -> dict | None:
    if not match_data.get("info", {}).get("teams"):
        return None
    if not match_data.get("info", {}).get("participants"):
        return None
    
    row = {}
    for participant in match_data["info"]["participants"]:
        prefix = "blue" if participant["teamId"] == 100 else "red"
        row[f"{prefix}_{participant['championName']}"] = 1
    row["blue_win"] = int(match_data["info"]["teams"][0]["win"])
    return row
