"""Tests for the CLI commands."""

import json

import pytest
from click.testing import CliRunner

from toktab.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestCLI:
    def test_help(self, runner):
        """Test --help shows usage."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "TokTab" in result.output
        assert "search" in result.output

    def test_version(self, runner):
        """Test --version shows version."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "toktab" in result.output

    def test_no_args_shows_help(self, runner):
        """Test running without args shows help."""
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "Usage:" in result.output


class TestModelCommand:
    def test_model_lookup(self, runner, httpx_mock):
        """Test looking up a model."""
        httpx_mock.add_response(
            json={
                "litellm_model_name": "gpt-4o",
                "litellm_provider": "openai",
                "input_cost_per_token": 0.0000025,
                "output_cost_per_token": 0.00001,
            }
        )

        result = runner.invoke(cli, ["gpt-4o"])

        assert result.exit_code == 0
        assert "gpt-4o" in result.output

    def test_model_json_output(self, runner, httpx_mock):
        """Test --json outputs valid JSON."""
        mock_data = {
            "litellm_model_name": "gpt-4o",
            "litellm_provider": "openai",
        }
        httpx_mock.add_response(json=mock_data)

        result = runner.invoke(cli, ["--json", "gpt-4o"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["litellm_model_name"] == "gpt-4o"

    def test_model_not_found(self, runner, httpx_mock):
        """Test error message for unknown model."""
        httpx_mock.add_response(status_code=404)

        result = runner.invoke(cli, ["nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output


class TestSearchCommand:
    def test_search(self, runner, httpx_mock):
        """Test search command."""
        httpx_mock.add_response(
            json={
                "results": [{"slug": "claude-3-opus", "provider": "anthropic"}],
                "query": "claude",
                "count": 1,
            }
        )

        result = runner.invoke(cli, ["search", "claude"])

        assert result.exit_code == 0
        assert "claude-3-opus" in result.output

    def test_search_with_limit(self, runner, httpx_mock):
        """Test search with --limit."""
        httpx_mock.add_response(
            json={"results": [], "query": "test", "count": 0}
        )

        result = runner.invoke(cli, ["search", "--limit", "5", "test"])

        assert result.exit_code == 0
        request = httpx_mock.get_request()
        assert "limit=5" in str(request.url)

    def test_search_json_output(self, runner, httpx_mock):
        """Test search --json outputs valid JSON."""
        mock_data = {"results": [], "query": "test", "count": 0}
        httpx_mock.add_response(json=mock_data)

        result = runner.invoke(cli, ["search", "--json", "test"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "results" in parsed
