import time
from typing import Any
from typing import cast

import requests

class RiotClient:
    """Handles all communication with the Riot API.

    This class is responsible for:
    - Building request URLs
    - Rate limiting
    - Retrying failed requests
    - Returning raw API response data

    It does NOT handle storage, parsing, or anything else.
    """

    URLS: dict[str, str] = {
        "base": "https://{region}.api.riotgames.com",
        "puuid": "/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}",
        "match_ids": "/lol/match/v5/matches/by-puuid/{puuid}/ids",
        "match_detail": "/lol/match/v5/matches/{match_id}",
    }

    def __init__(self, api_key: str, region: str = "americas", request_delay: float = 0.1, max_retries: int = 3):
        """Store config and build the base URL.

        Args:
            api_key: Your Riot API key.
            region: Regional routing value (americas, europe, asia, sea).
            request_delay: Seconds to wait between requests.
            max_retries: How many times to retry a failed request.
        """
        self.api_key = api_key
        self.region = region
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.base_url = self.URLS["base"].format(region=region)
        self.headers = {"X-Riot-Token": api_key}

    def _make_request(self, url: str, params: dict | None = None) -> dict[str, Any] | list | None:
        """Send a GET request with rate limiting, error handling, and retries.

        This is the ONLY method that calls requests.get().
        All public methods delegate to this.

        Args:
            url: The full URL to request.

        Returns:
            The parsed JSON response as a dict.

        Things to handle:
            - Sleep for self.request_delay before each call
            - 429 (rate limited): read Retry-After header, sleep, retry
            - 404 (not found): raise or return None (your choice)
            - 500/503 (server error): retry up to max_retriesfor
            - Timeouts: retry up to max_retries
        """
        for _ in range(self.max_retries):
            try:
                time.sleep(self.request_delay)
                response = requests.get(url=url, headers=self.headers, timeout = 10, params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429: # pyright: ignore[reportPossiblyUnboundVariable]
                    retry_after = int(response.headers.get("Retry-After", 1)) # pyright: ignore[reportPossiblyUnboundVariable]
                    print(f"Rate limited. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                elif response.status_code in [500, 503]: # pyright: ignore[reportPossiblyUnboundVariable]
                    print(f"Server error (status {response.status_code}). Retrying...") # pyright: ignore[reportPossiblyUnboundVariable]
                    time.sleep(self.request_delay)
                elif response.status_code == 404: # pyright: ignore[reportPossiblyUnboundVariable]
                    print(f"Resource not found (status 404). URL: {url}")
                    return None
                else:
                    print(f"HTTP error (status {response.status_code}): {e}") # pyright: ignore[reportPossiblyUnboundVariable]
                    raise
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}. Retrying...")
                time.sleep(self.request_delay)
        raise requests.exceptions.RequestException(f"Failed to get a successful response after {self.max_retries} attempts. URL: {url}")

    def get_puuid(self, game_name: str, tag_line: str) -> str | None:
        """Look up a player's PUUID by their Riot ID.

        Args:
            game_name: The player's game name (e.g. "Soup Lover").
            tag_line: The player's tag line (e.g. "ItLit"). No # symbol.

        Returns:
            The player's PUUID string.
        """
        url = self.base_url + self.URLS["puuid"].format(game_name=game_name, tag_line=tag_line)
        response = self._make_request(url)
        if isinstance(response, dict):
            return cast(str | None, response["puuid"])
        return None

    def get_match_ids(self, puuid: str, count: int = 20, queue: int = 420) -> list[str] | None:
        """Get recent match IDs for a player.

        Args:
            puuid: The player's PUUID.
            count: Number of match IDs to return (max 100).
            queue: Queue type. 420 = ranked solo/duo.

        Returns:
            A list of match ID strings.
        """
        url = self.base_url + self.URLS["match_ids"].format(puuid=puuid)
        response = self._make_request(url, params={"count": count, "queue": queue})
        return response if isinstance(response, list) else None

    def get_match_detail(self, match_id: str) -> dict[str, Any] | None:
        """Get full match data for a single match.

        Args:
            match_id: The match ID (e.g. "NA1_4567890123").

        Returns:
            The full match data dict.
        """
        url = self.base_url + self.URLS["match_detail"].format(match_id=match_id)
        response = self._make_request(url)
        if isinstance(response, dict):
            return response
        return None
