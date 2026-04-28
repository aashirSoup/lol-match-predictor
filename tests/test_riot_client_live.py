"""Live integration tests — these actually hit the Riot API.

Run sparingly to avoid burning rate limit.
Usage: pytest tests/test_riot_client_live.py -v

These tests require a valid RIOT_API_KEY environment variable.
"""

import os
import json
import pytest
from src.data_collection.riot_client import RiotClient

# Skip all tests in this file if no API key is set
API_KEY = os.getenv("RIOT_API_KEY")
pytestmark = pytest.mark.skipif(API_KEY is None, reason="RIOT_API_KEY not set")


@pytest.fixture
def client():
    """Create a RiotClient with the real API key."""
    return RiotClient(api_key=API_KEY, region="americas") # pyright: ignore[reportArgumentType]


# ---- Use your own Riot ID for these tests ----
TEST_GAME_NAME = "Soup Lover"
TEST_TAG_LINE = "ItLit"


class TestAccountLookup:
    def test_get_puuid_returns_string(self, client):
        """Looking up a real account should return a PUUID string."""
        puuid = client.get_puuid(TEST_GAME_NAME, TEST_TAG_LINE)
        assert isinstance(puuid, str)
        assert len(puuid) > 0

    def test_get_puuid_invalid_account_handles_gracefully(self, client):
        """Looking up a nonexistent account should not crash."""
        # TODO: call get_puuid with a fake name, verify it returns None or raises cleanly
        pass


class TestMatchHistory:
    def test_get_match_ids_returns_list(self, client):
        """Getting match IDs for a real player should return a list of strings."""
        puuid = client.get_puuid(TEST_GAME_NAME, TEST_TAG_LINE)
        match_ids = client.get_match_ids(puuid, count=5)
        assert isinstance(match_ids, list)
        assert len(match_ids) > 0
        assert all(isinstance(m, str) for m in match_ids)

    def test_get_match_ids_respects_count(self, client):
        """Requesting 3 matches should return at most 3."""
        puuid = client.get_puuid(TEST_GAME_NAME, TEST_TAG_LINE)
        match_ids = client.get_match_ids(puuid, count=3)
        assert len(match_ids) <= 3


class TestMatchDetail:
    def test_get_match_detail_returns_dict(self, client):
        """Fetching a real match should return a dict with expected keys."""
        puuid = client.get_puuid(TEST_GAME_NAME, TEST_TAG_LINE)
        match_ids = client.get_match_ids(puuid, count=1)
        match_data = client.get_match_detail(match_ids[0])
        assert isinstance(match_data, dict)
        assert "info" in match_data
        assert "metadata" in match_data


class TestSaveFixture:
    def test_save_sample_match_as_fixture(self, client):
        """Pull one real match and save it as a test fixture.

        Run this ONCE to generate tests/fixtures/sample_match.json,
        then use that file for your unit tests.
        """
        puuid = client.get_puuid(TEST_GAME_NAME, TEST_TAG_LINE)
        match_ids = client.get_match_ids(puuid, count=1)
        match_data = client.get_match_detail(match_ids[0])

        fixture_path = os.path.join("tests", "fixtures", "sample_match.json")
        os.makedirs(os.path.dirname(fixture_path), exist_ok=True)
        with open(fixture_path, "w") as f:
            json.dump(match_data, f, indent=2)

        assert os.path.exists(fixture_path)
        print(f"\nFixture saved to {fixture_path}")
        