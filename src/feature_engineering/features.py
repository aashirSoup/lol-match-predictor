"""Computes derived features from parsed match rows."""

_TIER_ORDER = {
    "IRON": 0,
    "BRONZE": 1,
    "SILVER": 2,
    "GOLD": 3,
    "PLATINUM": 4,
    "EMERALD": 5,
    "DIAMOND": 6,
    "MASTER": 7,
    "GRANDMASTER": 8,
    "CHALLENGER": 9,
}

_DIVISION_ORDER = {"IV": 0, "III": 1, "II": 2, "I": 3}

_LP_PER_DIVISION = 100
_DIVISIONS_PER_TIER = 4
_LP_PER_TIER = _LP_PER_DIVISION * _DIVISIONS_PER_TIER


def rank_to_numeric(rank_data: list) -> int:
    solo = next(
        (e for e in rank_data if e.get("queueType") == "RANKED_SOLO_5x5"),
        None,
    )
    if solo is None:
        return 0

    tier_lp = _TIER_ORDER[solo["tier"]] * _LP_PER_TIER
    division_lp = _DIVISION_ORDER.get(solo.get("rank", ""), 0) * _LP_PER_DIVISION
    return tier_lp + division_lp + solo["leaguePoints"]
