"""Tests for the MEV relay booster."""

from unittest.mock import MagicMock

import pytest

from staker.mev import Booster


class TestBooster:
    """Tests for Booster relay selection."""

    def test_get_relays_filters_bad_relays(self, mocker):
        """Verify that relays that fail to respond are filtered out."""
        booster = Booster()

        # Mock ping to return None for bad relays, varied times for good ones
        ping_times = iter(
            [
                0.08,
                0.10,
                0.12,
                0.09,
                0.11,
                0.10,
                0.08,
                0.12,
                0.09,
                0.11,
                0.08,
                0.10,
                0.12,
                0.09,
                0.11,
            ]
        )  # 5 trials x 3 good relays

        def mock_ping(relay):
            if "bad" in relay:
                return None
            return next(ping_times)

        mocker.patch.object(booster, "ping", side_effect=mock_ping)
        # Need at least 2 good relays for stdev calculation
        mocker.patch(
            "staker.mev.RELAYS",
            [
                "https://good.relay",
                "https://bad.relay",
                "https://another.good",
                "https://third.good",
            ],
        )
        mocker.patch("staker.mev.sleep")

        relays = booster.get_relays()

        assert "https://bad.relay" not in relays
        assert "https://good.relay" in relays
        assert "https://another.good" in relays

    def test_get_relays_returns_all_on_error(self, mocker):
        """Verify fallback to all relays when testing fails."""
        booster = Booster()

        # Mock ping to return None for all (simulating network failure)
        mocker.patch.object(booster, "ping", return_value=None)
        mocker.patch("staker.mev.RELAYS", ["https://relay1", "https://relay2"])
        mocker.patch("staker.mev.sleep")

        relays = booster.get_relays()

        # Should return original RELAYS as fallback
        assert relays == ["https://relay1", "https://relay2"]

    def test_ping_returns_response_time_on_success(self, mocker):
        """Verify ping returns elapsed time on successful request."""
        booster = Booster()

        mock_response = MagicMock()
        mock_response.ok = True
        mocker.patch("staker.mev.requests.get", return_value=mock_response)
        mocker.patch("staker.mev.time", side_effect=[1.0, 1.15])  # 150ms elapsed

        result = booster.ping("https://test.relay")

        assert result == pytest.approx(0.15, abs=0.01)

    def test_ping_returns_none_on_failure(self, mocker):
        """Verify ping returns None when request fails."""
        booster = Booster()

        mock_response = MagicMock()
        mock_response.ok = False
        mocker.patch("staker.mev.requests.get", return_value=mock_response)
        mocker.patch("staker.mev.time", side_effect=[1.0, 1.1])

        result = booster.ping("https://test.relay")

        assert result is None
