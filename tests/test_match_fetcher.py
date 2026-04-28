"""Tests for match_fetcher.py."""
import pytest
from unittest.mock import MagicMock, patch
from src.data_collection.match_fetcher import fetch_and_store_matches

_MATCH_EXISTS = "src.data_collection.match_fetcher.match_exists"
_SAVE_MATCH = "src.data_collection.match_fetcher.save_match"


def make_client(match_ids_by_puuid=None, match_details=None):
    client = MagicMock()
    ids_map = match_ids_by_puuid or {}
    details_map = match_details or {}
    client.get_match_ids.side_effect = lambda puuid, count, queue: ids_map.get(puuid)
    client.get_match_detail.side_effect = lambda match_id: details_map.get(match_id)
    return client


class TestFetchAndStoreMatches:
    def test_saves_each_new_match_to_disk(self):
        client = make_client(
            match_ids_by_puuid={"puuid1": ["NA1_1", "NA1_2"]},
            match_details={"NA1_1": {"info": {}}, "NA1_2": {"info": {}}},
        )
        with patch(_MATCH_EXISTS, return_value=False):
            with patch(_SAVE_MATCH) as mock_save:
                fetch_and_store_matches(client, ["puuid1"], count=2)
        assert mock_save.call_count == 2

    def test_returns_number_of_new_matches_saved(self):
        client = make_client(
            match_ids_by_puuid={"puuid1": ["NA1_1", "NA1_2"]},
            match_details={"NA1_1": {"info": {}}, "NA1_2": {"info": {}}},
        )
        with patch(_MATCH_EXISTS, return_value=False):
            with patch(_SAVE_MATCH):
                result = fetch_and_store_matches(client, ["puuid1"], count=2)
        assert result == 2

    def test_returns_zero_when_no_new_matches(self):
        client = make_client(
            match_ids_by_puuid={"puuid1": ["NA1_1"]},
            match_details={"NA1_1": {"info": {}}},
        )
        with patch(_MATCH_EXISTS, return_value=True):
            with patch(_SAVE_MATCH):
                result = fetch_and_store_matches(client, ["puuid1"])
        assert result == 0

    def test_returns_zero_with_empty_puuid_list(self):
        client = MagicMock()
        with patch(_MATCH_EXISTS, return_value=False):
            with patch(_SAVE_MATCH):
                result = fetch_and_store_matches(client, [])
        assert result == 0

    def test_skips_matches_already_on_disk(self):
        client = make_client(
            match_ids_by_puuid={"puuid1": ["NA1_1", "NA1_2"]},
            match_details={"NA1_1": {"info": {}}, "NA1_2": {"info": {}}},
        )
        with patch(_MATCH_EXISTS, return_value=True):
            with patch(_SAVE_MATCH) as mock_save:
                fetch_and_store_matches(client, ["puuid1"])
        mock_save.assert_not_called()

    def test_skips_duplicate_match_ids_across_players(self):
        client = make_client(
            match_ids_by_puuid={
                "puuid1": ["NA1_1", "NA1_2"],
                "puuid2": ["NA1_1", "NA1_3"],
            },
            match_details={
                "NA1_1": {"info": {}},
                "NA1_2": {"info": {}},
                "NA1_3": {"info": {}},
            },
        )
        with patch(_MATCH_EXISTS, return_value=False):
            with patch(_SAVE_MATCH) as mock_save:
                fetch_and_store_matches(client, ["puuid1", "puuid2"])
        saved_ids = [c.args[0] for c in mock_save.call_args_list]
        assert saved_ids.count("NA1_1") == 1
        assert len(saved_ids) == 3

    def test_skips_player_with_no_match_ids(self):
        client = make_client(
            match_ids_by_puuid={"puuid1": None, "puuid2": ["NA1_1"]},
            match_details={"NA1_1": {"info": {}}},
        )
        with patch(_MATCH_EXISTS, return_value=False):
            with patch(_SAVE_MATCH) as mock_save:
                fetch_and_store_matches(client, ["puuid1", "puuid2"])
        saved_ids = [c.args[0] for c in mock_save.call_args_list]
        assert saved_ids == ["NA1_1"]

    def test_skips_match_when_detail_fetch_returns_none(self):
        client = make_client(
            match_ids_by_puuid={"puuid1": ["NA1_1", "NA1_2"]},
            match_details={"NA1_1": None, "NA1_2": {"info": {}}},
        )
        with patch(_MATCH_EXISTS, return_value=False):
            with patch(_SAVE_MATCH) as mock_save:
                fetch_and_store_matches(client, ["puuid1"])
        saved_ids = [c.args[0] for c in mock_save.call_args_list]
        assert saved_ids == ["NA1_2"]

    def test_saves_to_data_raw_output_dir(self):
        client = make_client(
            match_ids_by_puuid={"puuid1": ["NA1_1"]},
            match_details={"NA1_1": {"info": {}}},
        )
        with patch(_MATCH_EXISTS, return_value=False):
            with patch(_SAVE_MATCH) as mock_save:
                fetch_and_store_matches(client, ["puuid1"])
        mock_save.assert_called_once_with("NA1_1", {"info": {}}, output_dir="data/raw")

    def test_fetches_match_ids_with_correct_count_and_ranked_queue(self):
        client = make_client(match_ids_by_puuid={"puuid1": []})
        with patch(_MATCH_EXISTS, return_value=False):
            with patch(_SAVE_MATCH):
                fetch_and_store_matches(client, ["puuid1"], count=5)
        client.get_match_ids.assert_called_once_with("puuid1", 5, 420)
