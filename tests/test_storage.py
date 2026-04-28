"""Tests for storage.py."""
import json
import pytest
from src.data_collection.storage import save_match, match_exists, load_match


class TestSaveMatch:
    def test_creates_json_file(self, tmp_path):
        save_match("NA1_123", {"key": "value"}, output_dir=str(tmp_path))
        assert (tmp_path / "NA1_123.json").exists()

    def test_file_content_matches_match_data(self, tmp_path):
        match_data = {"metadata": {"matchId": "NA1_123"}, "info": {"gameDuration": 1800}}
        save_match("NA1_123", match_data, output_dir=str(tmp_path))
        with open(tmp_path / "NA1_123.json") as f:
            loaded = json.load(f)
        assert loaded == match_data

    def test_creates_output_dir_if_not_present(self, tmp_path):
        nested = str(tmp_path / "new" / "nested")
        save_match("NA1_456", {}, output_dir=nested)
        assert (tmp_path / "new" / "nested").is_dir()

    def test_filename_uses_match_id_with_json_extension(self, tmp_path):
        save_match("NA1_999", {}, output_dir=str(tmp_path))
        files = list(tmp_path.iterdir())
        assert len(files) == 1
        assert files[0].name == "NA1_999.json"

    def test_overwrites_existing_file(self, tmp_path):
        save_match("NA1_123", {"version": 1}, output_dir=str(tmp_path))
        save_match("NA1_123", {"version": 2}, output_dir=str(tmp_path))
        with open(tmp_path / "NA1_123.json") as f:
            loaded = json.load(f)
        assert loaded == {"version": 2}


class TestMatchExists:
    def test_returns_true_when_file_exists(self, tmp_path):
        (tmp_path / "NA1_123.json").write_text("{}")
        assert match_exists("NA1_123", output_dir=str(tmp_path)) is True

    def test_returns_false_when_file_is_missing(self, tmp_path):
        assert match_exists("NA1_999", output_dir=str(tmp_path)) is False

    def test_returns_false_for_different_match_id(self, tmp_path):
        (tmp_path / "NA1_123.json").write_text("{}")
        assert match_exists("NA1_456", output_dir=str(tmp_path)) is False


class TestLoadMatch:
    def test_returns_match_data_as_dict(self, tmp_path):
        match_data = {"metadata": {"matchId": "NA1_123"}, "info": {"gameDuration": 900}}
        (tmp_path / "NA1_123.json").write_text(json.dumps(match_data))
        result = load_match("NA1_123", output_dir=str(tmp_path))
        assert result == match_data

    def test_raises_when_file_does_not_exist(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_match("NA1_999", output_dir=str(tmp_path))

    def test_save_and_load_roundtrip(self, tmp_path):
        match_data = {"participants": ["p1", "p2"], "gameId": 42}
        save_match("NA1_42", match_data, output_dir=str(tmp_path))
        assert load_match("NA1_42", output_dir=str(tmp_path)) == match_data
