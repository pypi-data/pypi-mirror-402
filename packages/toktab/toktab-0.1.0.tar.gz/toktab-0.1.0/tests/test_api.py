"""Tests for the TokTab API client."""

import pytest
import httpx

from toktab.api import (
    get_model,
    search,
    ModelNotFoundError,
    APIError,
    BASE_URL,
)


class TestGetModel:
    def test_get_model_success(self, httpx_mock):
        """Test successful model fetch."""
        mock_data = {
            "litellm_model_name": "gpt-4o",
            "litellm_provider": "openai",
            "input_cost_per_token": 0.0000025,
            "output_cost_per_token": 0.00001,
            "max_input_tokens": 128000,
        }
        httpx_mock.add_response(
            url=f"{BASE_URL}/gpt-4o/",
            json=mock_data,
        )

        result = get_model("gpt-4o")

        assert result["litellm_model_name"] == "gpt-4o"
        assert result["input_cost_per_token"] == 0.0000025

    def test_get_model_not_found(self, httpx_mock):
        """Test 404 response raises ModelNotFoundError."""
        httpx_mock.add_response(
            url=f"{BASE_URL}/nonexistent-model/",
            status_code=404,
        )

        with pytest.raises(ModelNotFoundError, match="not found"):
            get_model("nonexistent-model")

    def test_get_model_timeout(self, httpx_mock):
        """Test timeout raises APIError."""
        httpx_mock.add_exception(httpx.TimeoutException("timeout"))

        with pytest.raises(APIError, match="timed out"):
            get_model("gpt-4o")

    def test_get_model_network_error(self, httpx_mock):
        """Test network error raises APIError."""
        httpx_mock.add_exception(httpx.ConnectError("connection failed"))

        with pytest.raises(APIError, match="Network error"):
            get_model("gpt-4o")


class TestSearch:
    def test_search_success(self, httpx_mock):
        """Test successful search."""
        mock_data = {
            "results": [
                {
                    "name": "claude-3-opus",
                    "slug": "claude-3-opus",
                    "provider": "anthropic",
                    "input_cost_per_token": 0.000015,
                    "output_cost_per_token": 0.000075,
                }
            ],
            "query": "claude",
            "count": 1,
        }
        httpx_mock.add_response(json=mock_data)

        result = search("claude")

        assert result["count"] == 1
        assert result["results"][0]["provider"] == "anthropic"

    def test_search_with_limit(self, httpx_mock):
        """Test search respects limit parameter."""
        httpx_mock.add_response(json={"results": [], "query": "test", "count": 0})

        search("test", limit=10)

        request = httpx_mock.get_request()
        assert "limit=10" in str(request.url)

    def test_search_limit_capped_at_50(self, httpx_mock):
        """Test search caps limit at 50."""
        httpx_mock.add_response(json={"results": [], "query": "test", "count": 0})

        search("test", limit=100)

        request = httpx_mock.get_request()
        assert "limit=50" in str(request.url)

    def test_search_bad_request(self, httpx_mock):
        """Test 400 response raises APIError."""
        httpx_mock.add_response(status_code=400)

        with pytest.raises(APIError, match="Invalid search query"):
            search("")
