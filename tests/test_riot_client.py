"""Tests for riot_client.py."""
import pytest
from unittest.mock import MagicMock, patch, call
import requests
from src.data_collection.riot_client import RiotClient


def make_client(**overrides):
    kwargs = {"api_key": "test-key", "region": "americas", "request_delay": 0.0, "max_retries": 3}
    return RiotClient(**{**kwargs, **overrides})


def make_response(status_code=200, json_data=None, headers=None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data if json_data is not None else {}
    response.headers = headers if headers is not None else {}
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    else:
        response.raise_for_status.return_value = None
    return response


class TestRiotClientInit:
    def test_stores_api_key(self):
        client = make_client(api_key="my-key")
        assert client.api_key == "my-key"

    def test_builds_base_url_from_region(self):
        client = make_client(region="europe")
        assert client.base_url == "https://europe.api.riotgames.com"

    def test_sets_auth_header(self):
        client = make_client(api_key="my-key")
        assert client.headers == {"X-Riot-Token": "my-key"}

    def test_default_region_is_americas(self):
        client = RiotClient(api_key="key")
        assert client.region == "americas"

    def test_default_request_delay(self):
        client = RiotClient(api_key="key")
        assert client.request_delay == 0.1

    def test_default_max_retries(self):
        client = RiotClient(api_key="key")
        assert client.max_retries == 3


class TestMakeRequest:
    def test_returns_dict_on_success(self):
        client = make_client()
        with patch("requests.get", return_value=make_response(200, {"key": "value"})):
            with patch("time.sleep"):
                result = client._make_request("http://example.com")
        assert result == {"key": "value"}

    def test_can_return_list_response(self):
        client = make_client()
        with patch("requests.get", return_value=make_response(200, ["NA1_1", "NA1_2"])):
            with patch("time.sleep"):
                result = client._make_request("http://example.com")
        assert result == ["NA1_1", "NA1_2"]

    def test_sleeps_request_delay_before_each_request(self):
        client = make_client(request_delay=0.5)
        with patch("requests.get", return_value=make_response(200)):
            with patch("time.sleep") as mock_sleep:
                client._make_request("http://example.com")
        assert call(0.5) in mock_sleep.call_args_list

    def test_returns_none_on_404(self):
        client = make_client()
        with patch("requests.get", return_value=make_response(404)):
            with patch("time.sleep"):
                result = client._make_request("http://example.com")
        assert result is None

    def test_404_does_not_retry(self):
        client = make_client(max_retries=3)
        with patch("requests.get", return_value=make_response(404)) as mock_get:
            with patch("time.sleep"):
                client._make_request("http://example.com")
        assert mock_get.call_count == 1

    def test_429_sleeps_for_retry_after_header_value(self):
        client = make_client(max_retries=2)
        rate_limited = make_response(429, headers={"Retry-After": "5"})
        success = make_response(200, {"data": "ok"})
        with patch("requests.get", side_effect=[rate_limited, success]):
            with patch("time.sleep") as mock_sleep:
                result = client._make_request("http://example.com")
        assert call(5) in mock_sleep.call_args_list
        assert result == {"data": "ok"}

    def test_429_defaults_retry_after_to_1_when_header_missing(self):
        client = make_client(max_retries=2)
        rate_limited = make_response(429, headers={})
        success = make_response(200)
        with patch("requests.get", side_effect=[rate_limited, success]):
            with patch("time.sleep") as mock_sleep:
                client._make_request("http://example.com")
        assert call(1) in mock_sleep.call_args_list

    def test_500_retries_up_to_max_retries_then_raises(self):
        client = make_client(max_retries=3)
        with patch("requests.get", return_value=make_response(500)) as mock_get:
            with patch("time.sleep"):
                with pytest.raises(requests.exceptions.RequestException):
                    client._make_request("http://example.com")
        assert mock_get.call_count == 3

    def test_503_retries_up_to_max_retries_then_raises(self):
        client = make_client(max_retries=2)
        with patch("requests.get", return_value=make_response(503)) as mock_get:
            with patch("time.sleep"):
                with pytest.raises(requests.exceptions.RequestException):
                    client._make_request("http://example.com")
        assert mock_get.call_count == 2

    def test_server_error_then_success_returns_data(self):
        client = make_client(max_retries=3)
        with patch("requests.get", side_effect=[make_response(500), make_response(200, {"ok": True})]):
            with patch("time.sleep"):
                result = client._make_request("http://example.com")
        assert result == {"ok": True}

    def test_connection_error_retries_up_to_max_retries_then_raises(self):
        client = make_client(max_retries=3)
        with patch("requests.get", side_effect=requests.exceptions.ConnectionError()) as mock_get:
            with patch("time.sleep"):
                with pytest.raises(requests.exceptions.RequestException):
                    client._make_request("http://example.com")
        assert mock_get.call_count == 3

    def test_timeout_retries_up_to_max_retries_then_raises(self):
        client = make_client(max_retries=3)
        with patch("requests.get", side_effect=requests.exceptions.Timeout()) as mock_get:
            with patch("time.sleep"):
                with pytest.raises(requests.exceptions.RequestException):
                    client._make_request("http://example.com")
        assert mock_get.call_count == 3

    def test_non_retryable_http_error_raises_immediately(self):
        client = make_client(max_retries=3)
        with patch("requests.get", return_value=make_response(401)) as mock_get:
            with patch("time.sleep"):
                with pytest.raises(requests.exceptions.HTTPError):
                    client._make_request("http://example.com")
        assert mock_get.call_count == 1

    def test_passes_params_to_requests_get(self):
        client = make_client()
        with patch("requests.get", return_value=make_response(200, [])) as mock_get:
            with patch("time.sleep"):
                client._make_request("http://example.com", params={"count": 5, "queue": 420})
        mock_get.assert_called_once_with(
            url="http://example.com",
            headers={"X-Riot-Token": "test-key"},
            timeout=10,
            params={"count": 5, "queue": 420},
        )


class TestGetPuuid:
    def test_returns_puuid_string_from_response(self):
        client = make_client()
        with patch.object(client, "_make_request", return_value={"puuid": "abc-123", "gameName": "Test", "tagLine": "NA1"}):
            result = client.get_puuid("Test", "NA1")
        assert result == "abc-123"

    def test_returns_none_when_api_returns_none(self):
        client = make_client()
        with patch.object(client, "_make_request", return_value=None):
            result = client.get_puuid("NotExist", "NA1")
        assert result is None

    def test_returns_none_when_api_returns_list(self):
        client = make_client()
        with patch.object(client, "_make_request", return_value=["unexpected"]):
            result = client.get_puuid("Test", "NA1")
        assert result is None

    def test_builds_correct_url(self):
        client = make_client(region="americas")
        with patch.object(client, "_make_request", return_value={"puuid": "x"}) as mock_req:
            client.get_puuid("Soup Lover", "ItLit")
        expected = "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Soup Lover/ItLit"
        mock_req.assert_called_once_with(expected)


class TestGetMatchIds:
    def test_returns_list_from_response(self):
        client = make_client()
        with patch.object(client, "_make_request", return_value=["NA1_1", "NA1_2"]):
            result = client.get_match_ids("some-puuid")
        assert result == ["NA1_1", "NA1_2"]

    def test_returns_none_when_response_is_none(self):
        client = make_client()
        with patch.object(client, "_make_request", return_value=None):
            result = client.get_match_ids("some-puuid")
        assert result is None

    def test_returns_none_when_response_is_dict(self):
        client = make_client()
        with patch.object(client, "_make_request", return_value={"error": "unexpected"}):
            result = client.get_match_ids("some-puuid")
        assert result is None

    def test_passes_count_and_queue_as_params(self):
        client = make_client()
        with patch.object(client, "_make_request", return_value=[]) as mock_req:
            client.get_match_ids("some-puuid", count=10, queue=420)
        mock_req.assert_called_once_with(
            "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/some-puuid/ids",
            params={"count": 10, "queue": 420},
        )

    def test_default_count_is_20(self):
        client = make_client()
        with patch.object(client, "_make_request", return_value=[]) as mock_req:
            client.get_match_ids("some-puuid")
        params = mock_req.call_args[1]["params"]
        assert params["count"] == 20

    def test_default_queue_is_ranked_solo(self):
        client = make_client()
        with patch.object(client, "_make_request", return_value=[]) as mock_req:
            client.get_match_ids("some-puuid")
        params = mock_req.call_args[1]["params"]
        assert params["queue"] == 420

    def test_builds_correct_url(self):
        client = make_client(region="europe")
        with patch.object(client, "_make_request", return_value=[]) as mock_req:
            client.get_match_ids("test-puuid")
        url = mock_req.call_args[0][0]
        assert url == "https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/test-puuid/ids"


class TestGetMatchDetail:
    def test_returns_dict_from_response(self):
        client = make_client()
        match_data = {"metadata": {"matchId": "NA1_123"}, "info": {}}
        with patch.object(client, "_make_request", return_value=match_data):
            result = client.get_match_detail("NA1_123")
        assert result == match_data

    def test_returns_none_when_response_is_none(self):
        client = make_client()
        with patch.object(client, "_make_request", return_value=None):
            result = client.get_match_detail("NA1_123")
        assert result is None

    def test_returns_none_when_response_is_list(self):
        client = make_client()
        with patch.object(client, "_make_request", return_value=["unexpected"]):
            result = client.get_match_detail("NA1_123")
        assert result is None

    def test_builds_correct_url(self):
        client = make_client(region="americas")
        with patch.object(client, "_make_request", return_value={}) as mock_req:
            client.get_match_detail("NA1_5549104685")
        url = mock_req.call_args[0][0]
        assert url == "https://americas.api.riotgames.com/lol/match/v5/matches/NA1_5549104685"
