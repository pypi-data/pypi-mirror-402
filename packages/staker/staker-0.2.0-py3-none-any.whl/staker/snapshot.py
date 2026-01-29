"""EBS snapshot management for AWS-based Ethereum staking.

This module provides snapshot management capabilities for persisting blockchain
data on AWS EBS volumes, including backup rotation and launch template updates.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3
from botocore.exceptions import ClientError

from staker.config import AWS, DEPLOY_ENV, MAX_SNAPSHOT_DAYS, SNAPSHOT_DAYS


class SnapshotManager(ABC):
    """Abstract base class for snapshot management.

    This interface allows for different snapshot implementations,
    enabling dependency injection for testing and local development.
    """

    @abstractmethod
    def backup(self) -> dict[str, Any] | None:
        """Create a backup snapshot if needed.

        Returns:
            The created snapshot dict, or None if no backup was needed.
        """
        ...

    @abstractmethod
    def is_older_than(self, snapshot: dict[str, Any] | None, num_days: int) -> bool:
        """Check if a snapshot is older than the given number of days.

        Args:
            snapshot: The snapshot to check.
            num_days: Maximum age in days.

        Returns:
            True if the snapshot is older than num_days.
        """
        ...

    @abstractmethod
    def update(self) -> bool:
        """Update launch template with latest snapshot.

        Returns:
            True if an instance refresh is needed.
        """
        ...

    @abstractmethod
    def instance_is_draining(self) -> bool:
        """Check if the ECS container instance is draining.

        Returns:
            True if the instance is in DRAINING status.
        """
        ...

    @abstractmethod
    def force_create(self) -> dict[str, Any] | None:
        """Force create a new snapshot immediately.

        Returns:
            The created snapshot dict.
        """
        ...

    @abstractmethod
    def terminate(self) -> None:
        """Terminate the current EC2 instance."""
        ...


class NoOpSnapshotManager(SnapshotManager):
    """No-op implementation for local development.

    All methods return safe default values, allowing the staker
    to run without AWS infrastructure.
    """

    def backup(self) -> None:
        """No-op backup."""
        return None

    def is_older_than(self, snapshot: dict[str, Any] | None, num_days: int) -> bool:
        """Always returns False (never triggers backup)."""
        return False

    def update(self) -> bool:
        """No-op update."""
        return False

    def instance_is_draining(self) -> bool:
        """Always returns False."""
        return False

    def force_create(self) -> None:
        """No-op create."""
        return None

    def terminate(self) -> None:
        """No-op terminate."""
        pass


class Snapshot(SnapshotManager):
    """AWS EBS snapshot manager for blockchain data persistence.

    Manages EBS snapshots for the staking node, including:
    - Periodic backup creation
    - Snapshot rotation and cleanup
    - Launch template updates for new instances
    """

    def __init__(self) -> None:
        """Initialize AWS clients and load instance metadata."""
        self.tag = f"{DEPLOY_ENV}_staking_snapshot"
        self.ec2 = boto3.client("ec2")
        self.ssm = boto3.client("ssm")
        self.auto = boto3.client("autoscaling")
        self.ecs = boto3.client("ecs")
        self.volume_id: str = ""
        self.instance_id: str = ""
        if AWS:
            self.volume_id = self._get_prefix_id("VOLUME")
            self.instance_id = self._get_prefix_id("INSTANCE")

    def is_older_than(self, snapshot: dict[str, Any] | None, num_days: int) -> bool:
        """Check if a snapshot is older than the given number of days."""
        if snapshot is None:
            return True
        created = self._get_snapshot_time(snapshot)
        now = datetime.now(UTC).replace(tzinfo=None)
        actual_delta = now - created
        max_delta = timedelta(days=num_days)
        return actual_delta > max_delta

    def force_create(self) -> dict[str, Any]:
        """Force create a new snapshot immediately."""
        snapshot = self.ec2.create_snapshot(
            VolumeId=self.volume_id,
            TagSpecifications=[
                {"ResourceType": "snapshot", "Tags": [{"Key": "type", "Value": self.tag}]}
            ],
        )
        return snapshot

    def _create(self, curr_snapshots: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Create a snapshot if all existing ones are old enough.

        Args:
            curr_snapshots: List of current snapshots.

        Returns:
            The new snapshot if created, None otherwise.
        """
        all_snapshots_are_old = all(
            self.is_older_than(snapshot, SNAPSHOT_DAYS) for snapshot in curr_snapshots
        )
        if all_snapshots_are_old:
            snapshot = self.force_create()
            self._put_param(snapshot["SnapshotId"])
            return snapshot
        return None

    def _get_prefix_id(self, prefix: str) -> str:
        """Read an ID file from the EBS volume.

        Note: These files are created by the CloudFormation template's
        user data script (see template.yaml UserData).

        Args:
            prefix: The prefix (VOLUME or INSTANCE).

        Returns:
            The ID value from the file.
        """
        with open(f"/mnt/ebs/{prefix}_ID") as file:
            return file.read().strip()

    def _get_snapshots(self) -> list[dict[str, Any]]:
        """Get all snapshots with the staking tag."""
        snapshots = self.ec2.describe_snapshots(
            Filters=[
                {"Name": "tag:type", "Values": [self.tag]},
            ],
            OwnerIds=["self"],
        )["Snapshots"]
        return snapshots

    def _get_exceptions(self) -> set[str]:
        """Get snapshot IDs that should not be purged."""
        exceptions = {
            exception
            for exception in [self._get_param(), self._get_curr_snapshot_id()]
            if exception
        }
        return exceptions

    def _get_snapshot_time(self, snapshot: dict[str, Any]) -> datetime:
        """Extract creation time from a snapshot."""
        return snapshot["StartTime"].replace(tzinfo=None)

    def _find_most_recent(self, curr_snapshots: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Find the most recently created snapshot."""
        if not curr_snapshots:
            return None
        return max(curr_snapshots, key=self._get_snapshot_time)

    def _purge(self, curr_snapshots: list[dict[str, Any]], exceptions: set[str]) -> None:
        """Delete old snapshots that are not protected.

        Args:
            curr_snapshots: List of current snapshots.
            exceptions: Set of snapshot IDs to keep.
        """
        purgeable = [
            snapshot
            for snapshot in curr_snapshots
            if self.is_older_than(snapshot, MAX_SNAPSHOT_DAYS)
            and snapshot["SnapshotId"] not in exceptions
        ]

        for snapshot in purgeable:
            self.ec2.delete_snapshot(SnapshotId=snapshot["SnapshotId"])

    def _put_param(self, snapshot_id: str) -> None:
        """Store snapshot ID in SSM Parameter Store."""
        self.ssm.put_parameter(
            Name=self.tag,
            Value=snapshot_id,
            Type="String",
            Overwrite=True,
            Tier="Standard",
            DataType="text",
        )

    def _get_param(self) -> str | None:
        """Get snapshot ID from SSM Parameter Store."""
        try:
            return self.ssm.get_parameter(Name=self.tag)["Parameter"]["Value"]
        except ClientError as e:
            logging.exception(e)
            return None

    def _get_curr_snapshot_id(self) -> str | None:
        """Get snapshot ID from current instance's launch template."""
        try:
            if AWS:
                launch_template = self.ec2.get_launch_template_data(InstanceId=self.instance_id)
                for device in launch_template["LaunchTemplateData"]["BlockDeviceMappings"]:
                    if device["DeviceName"] == "/dev/sdx":
                        return device["Ebs"]["SnapshotId"]
        except ClientError as e:
            logging.exception(e)
        return None

    def update(self) -> bool:
        """Update launch template with latest snapshot.

        Returns:
            True if the instance needs to be refreshed.
        """
        curr_snapshots = self._get_snapshots()
        most_recent = self._find_most_recent(curr_snapshots) or {}
        recent_snapshot_id = most_recent.get("SnapshotId")

        if recent_snapshot_id and self._get_param() != recent_snapshot_id:
            self._put_param(recent_snapshot_id)

        template_name = f"{DEPLOY_ENV}_launch_template"
        launch_template = self.ec2.describe_launch_template_versions(
            LaunchTemplateName=template_name,
            Versions=["$Latest"],
        )["LaunchTemplateVersions"][0]

        vol = None
        curr_snapshot_id = None
        for device in launch_template["LaunchTemplateData"]["BlockDeviceMappings"]:
            if device["DeviceName"] == "/dev/sdx":
                vol = device
                curr_snapshot_id = device["Ebs"].get("SnapshotId")
                break

        template_version = str(launch_template["VersionNumber"])

        if recent_snapshot_id and curr_snapshot_id != recent_snapshot_id and vol:
            vol["Ebs"]["SnapshotId"] = recent_snapshot_id
            new_template = self.ec2.create_launch_template_version(
                LaunchTemplateName=template_name,
                SourceVersion=template_version,
                LaunchTemplateData={"BlockDeviceMappings": [vol]},
            )
            template_version = str(new_template["LaunchTemplateVersion"]["VersionNumber"])

        asg_name = f"ECS_{DEPLOY_ENV}_staking_ASG"
        asg = self.auto.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])[
            "AutoScalingGroups"
        ][0]

        def is_latest_version(curr_version: str, latest_version: str) -> bool:
            return curr_version == latest_version or curr_version == "$Latest"

        update_asg = not is_latest_version(
            str(asg["LaunchTemplate"]["Version"]),
            template_version,
        )

        instance = next(
            (inst for inst in asg["Instances"] if inst["InstanceId"] == self.instance_id),
            None,
        )
        refresh_instance = (
            not is_latest_version(
                str(instance["LaunchTemplate"]["Version"]),
                template_version,
            )
            if instance
            else False
        )

        if update_asg:
            self.auto.update_auto_scaling_group(
                AutoScalingGroupName=asg_name,
                LaunchTemplate={"LaunchTemplateName": template_name, "Version": "$Latest"},
            )

        return update_asg or refresh_instance

    def instance_is_draining(self) -> bool:
        """Check if the ECS container instance is draining."""
        cluster_name = f"{DEPLOY_ENV}-staking-cluster"
        container_instance_arns = self.ecs.list_container_instances(cluster=cluster_name)[
            "containerInstanceArns"
        ]
        container_instances = self.ecs.describe_container_instances(
            cluster=cluster_name,
            containerInstances=container_instance_arns,
        )["containerInstances"]
        container_instance = next(
            (inst for inst in container_instances if inst["ec2InstanceId"] == self.instance_id),
            None,
        )
        return container_instance["status"] == "DRAINING" if container_instance else False

    def backup(self) -> dict[str, Any] | None:
        """Create a backup snapshot if needed.

        Returns:
            The new or most recent snapshot.
        """
        curr_snapshots = self._get_snapshots()
        exceptions = self._get_exceptions()
        snapshot = self._create(curr_snapshots)
        self._purge(curr_snapshots, exceptions)
        return snapshot or self._find_most_recent(curr_snapshots)

    def terminate(self) -> None:
        """Terminate the current EC2 instance."""
        self.ec2.terminate_instances(InstanceIds=[self.instance_id])
