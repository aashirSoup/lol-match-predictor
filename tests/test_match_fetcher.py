"""Tests for match_fetcher.py."""
import json
import pytest
from unittest.mock import MagicMock, patch, call
from src.data_collection.match_fetcher import (
    fetch_and_store_matches,
    extract_puuids_from_match,
    collect_unique_puuids,
    snowball_collect,
)

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


_MATCH_DATA = {
    "metadata": {
        "participants": ["puuid-a", "puuid-b", "puuid-c", "puuid-d", "puuid-e",
                         "puuid-f", "puuid-g", "puuid-h", "puuid-i", "puuid-j"]
    }
}


class TestExtractPuuidsFromMatch:
    def test_returns_all_ten_participant_puuids(self):
        result = extract_puuids_from_match(_MATCH_DATA)
        assert result == _MATCH_DATA["metadata"]["participants"]

    def test_returns_list_type(self):
        result = extract_puuids_from_match(_MATCH_DATA)
        assert isinstance(result, list)

    def test_raises_key_error_when_metadata_missing(self):
        with pytest.raises(KeyError):
            extract_puuids_from_match({})

    def test_raises_key_error_when_participants_missing(self):
        with pytest.raises(KeyError):
            extract_puuids_from_match({"metadata": {}})

    def test_preserves_puuid_order(self):
        ordered = [f"puuid-{i}" for i in range(10)]
        match = {"metadata": {"participants": ordered}}
        assert extract_puuids_from_match(match) == ordered


class TestCollectUniquePuuids:
    def test_returns_all_puuids_from_single_file(self, tmp_path):
        match_file = tmp_path / "NA1_1.json"
        match_file.write_text(json.dumps(_MATCH_DATA), encoding="utf-8")

        result = collect_unique_puuids(str(tmp_path))

        assert result == set(_MATCH_DATA["metadata"]["participants"])

    def test_deduplicates_puuids_across_files(self, tmp_path):
        shared_puuid = "puuid-a"
        match1 = {"metadata": {"participants": [shared_puuid, "puuid-x"]}}
        match2 = {"metadata": {"participants": [shared_puuid, "puuid-y"]}}
        (tmp_path / "NA1_1.json").write_text(json.dumps(match1), encoding="utf-8")
        (tmp_path / "NA1_2.json").write_text(json.dumps(match2), encoding="utf-8")

        result = collect_unique_puuids(str(tmp_path))

        assert result == {shared_puuid, "puuid-x", "puuid-y"}

    def test_returns_empty_set_for_empty_directory(self, tmp_path):
        result = collect_unique_puuids(str(tmp_path))
        assert result == set()

    def test_ignores_non_json_files(self, tmp_path):
        (tmp_path / "notes.txt").write_text("not json", encoding="utf-8")
        result = collect_unique_puuids(str(tmp_path))
        assert result == set()

    def test_returns_set_type(self, tmp_path):
        match_file = tmp_path / "NA1_1.json"
        match_file.write_text(json.dumps(_MATCH_DATA), encoding="utf-8")
        result = collect_unique_puuids(str(tmp_path))
        assert isinstance(result, set)


_COLLECT_PUUIDS = "src.data_collection.match_fetcher.collect_unique_puuids"
_FETCH_AND_STORE = "src.data_collection.match_fetcher.fetch_and_store_matches"


class TestSnowballCollect:
    def test_returns_total_matches_saved_across_rounds(self, tmp_path):
        # Round 1 discovers puuid-a; round 2 discovers puuid-b (new player).
        with patch(_COLLECT_PUUIDS, side_effect=[{"puuid-a"}, {"puuid-a", "puuid-b"}]):
            with patch(_FETCH_AND_STORE, return_value=5):
                result = snowball_collect(MagicMock(), rounds=2, output_dir=str(tmp_path))
        assert result == 10

    def test_stops_early_when_no_new_puuids_found(self, tmp_path):
        with patch(_COLLECT_PUUIDS, return_value={"puuid-a"}):
            with patch(_FETCH_AND_STORE, return_value=1) as mock_fetch:
                snowball_collect(MagicMock(), rounds=3, output_dir=str(tmp_path))
        assert mock_fetch.call_count == 1

    def test_does_not_reprocess_already_seen_puuids(self, tmp_path):
        puuids_round1 = {"puuid-a"}
        puuids_round2 = {"puuid-a", "puuid-b"}
        side_effects = [puuids_round1, puuids_round2]

        with patch(_COLLECT_PUUIDS, side_effect=side_effects):
            with patch(_FETCH_AND_STORE, return_value=1) as mock_fetch:
                snowball_collect(MagicMock(), rounds=2, output_dir=str(tmp_path))

        _, second_call_puuids, _ = mock_fetch.call_args_list[1].args
        assert "puuid-a" not in second_call_puuids
        assert "puuid-b" in second_call_puuids

    def test_passes_matches_per_player_to_fetch(self, tmp_path):
        with patch(_COLLECT_PUUIDS, return_value={"puuid-a"}):
            with patch(_FETCH_AND_STORE, return_value=1) as mock_fetch:
                snowball_collect(MagicMock(), rounds=1, matches_per_player=10, output_dir=str(tmp_path))
        _, _, count = mock_fetch.call_args.args
        assert count == 10

    def test_returns_zero_when_no_puuids_exist_from_the_start(self, tmp_path):
        with patch(_COLLECT_PUUIDS, return_value=set()):
            with patch(_FETCH_AND_STORE, return_value=0) as mock_fetch:
                result = snowball_collect(MagicMock(), rounds=3, output_dir=str(tmp_path))
        mock_fetch.assert_not_called()
        assert result == 0

    def test_creates_output_directory_if_missing(self, tmp_path):
        new_dir = tmp_path / "deep" / "nested"
        with patch(_COLLECT_PUUIDS, return_value=set()):
            with patch(_FETCH_AND_STORE, return_value=0):
                snowball_collect(MagicMock(), rounds=1, output_dir=str(new_dir))
        assert new_dir.exists()
