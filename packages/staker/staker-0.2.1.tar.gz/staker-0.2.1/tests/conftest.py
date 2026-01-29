"""Pytest fixtures for Ethereum staking node tests."""

import os

import pytest

# Set required environment variables before importing any modules
os.environ.setdefault("DEPLOY_ENV", "dev")
os.environ.setdefault("ETH_ADDR", "0x0000000000000000000000000000000000000000")

from staker.environment import Environment


class MockEnvironment(Environment):
    """Mock environment for testing."""

    def __init__(
        self,
        logs_path: str = "/tmp/test_logs.txt",
        data_prefix: str = "/tmp/test_data",
        p2p_host: str | None = None,
        colored_logs: bool = False,
        manage_snapshots: bool = False,
    ):
        self._logs_path = logs_path
        self._data_prefix = data_prefix
        self._p2p_host = p2p_host
        self._colored_logs = colored_logs
        self._manage_snapshots = manage_snapshots

    def get_logs_path(self) -> str:
        return self._logs_path

    def get_data_prefix(self) -> str:
        return self._data_prefix

    def get_p2p_host_dns(self, is_dev: bool) -> str | None:
        return self._p2p_host

    def use_colored_logs(self) -> bool:
        return self._colored_logs

    def should_manage_snapshots(self) -> bool:
        return self._manage_snapshots


@pytest.fixture
def mock_env():
    """Provide a mock environment for tests."""
    return MockEnvironment()


@pytest.fixture
def mock_env_with_snapshots():
    """Provide a mock environment with snapshot management enabled."""
    return MockEnvironment(manage_snapshots=True)
