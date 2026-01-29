"""Runtime environment abstraction for the Ethereum staking node.

This module provides abstractions for runtime-specific configurations,
allowing the same code to run on AWS or locally with appropriate settings.
"""

import os
from abc import ABC, abstractmethod


class Environment(ABC):
    """Abstract base class for runtime environment configuration.

    This abstracts the differences between running on AWS (container)
    vs locally, separate from network choice (dev/prod).
    """

    @abstractmethod
    def get_logs_path(self) -> str:
        """Get the path to the logs file.

        Returns:
            Absolute path to the logs file.
        """
        ...

    @abstractmethod
    def get_data_prefix(self) -> str:
        """Get the base directory for data (geth, prysm data dirs).

        Returns:
            Path prefix for data directories.
        """
        ...

    @abstractmethod
    def get_p2p_host_dns(self, is_dev: bool) -> str | None:
        """Get P2P host DNS for beacon chain.

        Args:
            is_dev: Whether running in dev/testnet mode.

        Returns:
            The DNS hostname, or None if not applicable.
        """
        ...

    @abstractmethod
    def use_colored_logs(self) -> bool:
        """Whether to use colored console output.

        Returns:
            True if colored output should be used.
        """
        ...

    @abstractmethod
    def should_manage_snapshots(self) -> bool:
        """Whether to manage EBS snapshots.

        Returns:
            True if snapshot management is enabled.
        """
        ...


class AWSEnvironment(Environment):
    """Runtime environment for AWS ECS containers."""

    def get_logs_path(self) -> str:
        """Get logs path for AWS environment."""
        return "/mnt/ebs/logs.txt"

    def get_data_prefix(self) -> str:
        """Get data prefix for AWS environment."""
        return "/mnt/ebs"

    def get_p2p_host_dns(self, is_dev: bool) -> str:
        """Get P2P host DNS for AWS environment."""
        # return f"aws.{'dev.' if is_dev else ''}eth.machine.one"
        return None

    def use_colored_logs(self) -> bool:
        """AWS uses plain logs for CloudWatch."""
        return False

    def should_manage_snapshots(self) -> bool:
        """AWS environment manages EBS snapshots."""
        return True


class LocalEnvironment(Environment):
    """Runtime environment for local development."""

    def get_logs_path(self) -> str:
        """Get logs path for local environment."""
        return "/mnt/ebs/ethereum/logs.txt"

    def get_data_prefix(self) -> str:
        """Get data prefix for local environment (home directory)."""
        return os.path.expanduser("~")

    def get_p2p_host_dns(self, is_dev: bool) -> str | None:
        """Local environment doesn't use P2P host DNS."""
        return None

    def use_colored_logs(self) -> bool:
        """Local environment uses colored logs."""
        return True

    def should_manage_snapshots(self) -> bool:
        """Local environment doesn't manage snapshots."""
        return False


def get_environment() -> Environment:
    """Factory function to get the appropriate environment.

    Returns:
        AWSEnvironment if AWS env var is set, otherwise LocalEnvironment.
    """
    from staker.config import AWS

    return AWSEnvironment() if AWS else LocalEnvironment()
