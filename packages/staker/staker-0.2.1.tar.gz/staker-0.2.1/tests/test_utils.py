"""Tests for utility functions."""

from unittest.mock import MagicMock

import requests

from staker.utils import colorize_log, get_public_ip


class TestColorizeLog:
    """Tests for colorize_log function."""

    def test_colorizes_execution(self):
        result = colorize_log("EXECUTION started")
        assert "[bold magenta]EXECUTION[/bold magenta]" in result

    def test_colorizes_consensus(self):
        result = colorize_log("CONSENSUS syncing")
        assert "[bold cyan]CONSENSUS[/bold cyan]" in result

    def test_colorizes_validation(self):
        result = colorize_log("VALIDATION active")
        assert "[bold yellow]VALIDATION[/bold yellow]" in result

    def test_colorizes_mev_boost(self):
        result = colorize_log("MEV_BOOST connected")
        assert "[bold green]MEV_BOOST[/bold green]" in result

    def test_colorizes_info_level(self):
        result = colorize_log("level=info msg=test")
        assert "[green]level=info[/green]" in result

    def test_colorizes_warning_level(self):
        result = colorize_log("level=warning msg=test")
        assert "[bright_yellow]level=warning[/bright_yellow]" in result

    def test_colorizes_error_level(self):
        result = colorize_log("level=error msg=test")
        assert "[bright_red]level=error[/bright_red]" in result

    def test_no_color_for_unknown(self):
        result = colorize_log("some random text")
        assert result == "some random text"


class TestGetPublicIp:
    """Tests for get_public_ip function."""

    def test_returns_ip_on_first_try(self, mocker):
        mock_response = MagicMock()
        mock_response.text = "1.2.3.4"
        mocker.patch("staker.utils.requests.get", return_value=mock_response)

        result = get_public_ip()

        assert result == "1.2.3.4"

    def test_retries_on_failure(self, mocker):
        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.text = "5.6.7.8"

        mocker.patch(
            "staker.utils.requests.get",
            side_effect=[
                requests.exceptions.RequestException("Connection error"),
                mock_response,
            ],
        )
        mock_print = mocker.patch("builtins.print")

        result = get_public_ip()

        assert result == "5.6.7.8"
        mock_print.assert_called_once()
        assert "trying alternate" in str(mock_print.call_args)

    def test_alternates_domains(self, mocker):
        # Both domains fail once each, then second succeeds
        mock_response = MagicMock()
        mock_response.text = "9.10.11.12"

        mocker.patch(
            "staker.utils.requests.get",
            side_effect=[
                requests.exceptions.RequestException("Fail 1"),
                requests.exceptions.RequestException("Fail 2"),
                mock_response,
            ],
        )
        mocker.patch("builtins.print")

        result = get_public_ip()

        assert result == "9.10.11.12"
