"""Tests for configuration module."""

import os

from staker.config import (
    DEV,
    DOCKER,
    LOG_STYLES,
    RELAYS,
    RELAYS_HOODI,
    RELAYS_MAINNET,
    get_env_bool,
)


class TestGetEnvBool:
    """Tests for get_env_bool function."""

    def test_returns_true_for_true_string(self, monkeypatch):
        monkeypatch.setenv("TEST_VAR", "true")
        assert get_env_bool("TEST_VAR") is True

    def test_returns_true_for_TRUE_string(self, monkeypatch):
        monkeypatch.setenv("TEST_VAR", "TRUE")
        assert get_env_bool("TEST_VAR") is True

    def test_returns_false_for_false_string(self, monkeypatch):
        monkeypatch.setenv("TEST_VAR", "false")
        assert get_env_bool("TEST_VAR") is False

    def test_returns_false_for_missing_var(self):
        # Ensure var doesn't exist
        os.environ.pop("NONEXISTENT_VAR", None)
        assert get_env_bool("NONEXISTENT_VAR") is False

    def test_returns_false_for_empty_string(self, monkeypatch):
        monkeypatch.setenv("TEST_VAR", "")
        assert get_env_bool("TEST_VAR") is False


class TestConstants:
    """Tests for configuration constants."""

    def test_log_styles_has_expected_keys(self):
        expected_keys = [
            "OPENVPN",
            "EXECUTION",
            "CONSENSUS",
            "VALIDATION",
            "MEV_BOOST",
            "INFO",
            "ERROR",
        ]
        for key in expected_keys:
            assert key in LOG_STYLES

    def test_relays_mainnet_not_empty(self):
        assert len(RELAYS_MAINNET) > 0

    def test_relays_hoodi_not_empty(self):
        assert len(RELAYS_HOODI) > 0

    def test_relays_matches_dev_setting(self):
        if DEV:
            assert RELAYS == RELAYS_HOODI
        else:
            assert RELAYS == RELAYS_MAINNET

    def test_docker_is_bool(self):
        assert isinstance(DOCKER, bool)
