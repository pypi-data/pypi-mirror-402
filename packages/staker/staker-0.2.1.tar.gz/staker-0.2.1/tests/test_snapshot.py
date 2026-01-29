"""Tests for snapshot management."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from staker.snapshot import NoOpSnapshotManager, Snapshot


class TestNoOpSnapshotManager:
    """Tests for NoOpSnapshotManager."""

    def test_backup_returns_none(self):
        manager = NoOpSnapshotManager()
        assert manager.backup() is None

    def test_is_older_than_returns_false(self):
        manager = NoOpSnapshotManager()
        assert manager.is_older_than(None, 30) is False
        assert manager.is_older_than({}, 30) is False

    def test_update_returns_false(self):
        manager = NoOpSnapshotManager()
        assert manager.update() is False

    def test_instance_is_draining_returns_false(self):
        manager = NoOpSnapshotManager()
        assert manager.instance_is_draining() is False

    def test_force_create_returns_none(self):
        manager = NoOpSnapshotManager()
        assert manager.force_create() is None

    def test_terminate_does_nothing(self):
        manager = NoOpSnapshotManager()
        # Should not raise
        manager.terminate()


class TestSnapshot:
    """Tests for Snapshot class."""

    @pytest.fixture
    def mock_boto3(self, mocker):
        """Mock boto3 clients."""
        mocker.patch("staker.snapshot.boto3.client")
        mocker.patch("staker.snapshot.AWS", False)  # Prevent file reads
        return mocker

    def test_is_older_than_none(self, mock_boto3):
        snapshot = Snapshot()
        assert snapshot.is_older_than(None, 30) is True

    def test_is_older_than_recent(self, mock_boto3):
        snapshot = Snapshot()
        recent_snap = {"StartTime": datetime.now(UTC)}
        assert snapshot.is_older_than(recent_snap, 30) is False

    def test_is_older_than_old(self, mock_boto3):
        snapshot = Snapshot()
        old_snap = {"StartTime": datetime.now(UTC) - timedelta(days=60)}
        assert snapshot.is_older_than(old_snap, 30) is True

    def test_is_older_than_exactly_at_limit(self, mock_boto3):
        snapshot = Snapshot()
        # Just under 30 days
        almost_old = {"StartTime": datetime.now(UTC) - timedelta(days=29, hours=23)}
        assert snapshot.is_older_than(almost_old, 30) is False

    def test_force_create_calls_ec2(self, mock_boto3, mocker):
        mock_ec2 = MagicMock()
        mock_ec2.create_snapshot.return_value = {"SnapshotId": "snap-123"}
        mocker.patch("staker.snapshot.boto3.client", return_value=mock_ec2)

        snapshot = Snapshot()
        snapshot.volume_id = "vol-abc"
        result = snapshot.force_create()

        mock_ec2.create_snapshot.assert_called_once()
        assert result["SnapshotId"] == "snap-123"

    def test_get_snapshots(self, mock_boto3, mocker):
        mock_ec2 = MagicMock()
        mock_ec2.describe_snapshots.return_value = {
            "Snapshots": [{"SnapshotId": "snap-1"}, {"SnapshotId": "snap-2"}]
        }
        mocker.patch("staker.snapshot.boto3.client", return_value=mock_ec2)

        snapshot = Snapshot()
        snapshots = snapshot._get_snapshots()

        assert len(snapshots) == 2
        assert snapshots[0]["SnapshotId"] == "snap-1"

    def test_find_most_recent_empty(self, mock_boto3):
        snapshot = Snapshot()
        result = snapshot._find_most_recent([])
        assert result is None

    def test_find_most_recent_returns_newest(self, mock_boto3):
        snapshot = Snapshot()
        snaps = [
            {"SnapshotId": "old", "StartTime": datetime.now(UTC) - timedelta(days=10)},
            {"SnapshotId": "new", "StartTime": datetime.now(UTC)},
            {"SnapshotId": "mid", "StartTime": datetime.now(UTC) - timedelta(days=5)},
        ]
        result = snapshot._find_most_recent(snaps)
        assert result["SnapshotId"] == "new"

    def test_put_param(self, mock_boto3, mocker):
        mock_ssm = MagicMock()
        mocker.patch("staker.snapshot.boto3.client", return_value=mock_ssm)

        snapshot = Snapshot()
        snapshot._put_param("snap-123")

        mock_ssm.put_parameter.assert_called_once()

    def test_get_param_returns_value(self, mock_boto3, mocker):
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "snap-xyz"}}
        mocker.patch("staker.snapshot.boto3.client", return_value=mock_ssm)

        snapshot = Snapshot()
        result = snapshot._get_param()

        assert result == "snap-xyz"

    def test_get_param_returns_none_on_error(self, mock_boto3, mocker):
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {"Error": {"Code": "ParameterNotFound", "Message": "Not found"}}, "GetParameter"
        )
        mocker.patch("staker.snapshot.boto3.client", return_value=mock_ssm)

        snapshot = Snapshot()
        result = snapshot._get_param()

        assert result is None

    def test_purge_deletes_old_snapshots(self, mock_boto3, mocker):
        mock_ec2 = MagicMock()
        mocker.patch("staker.snapshot.boto3.client", return_value=mock_ec2)
        mocker.patch("staker.snapshot.MAX_SNAPSHOT_DAYS", 30)

        snapshot = Snapshot()
        old_snap = {
            "SnapshotId": "snap-old",
            "StartTime": datetime.now(UTC) - timedelta(days=100),
        }
        exceptions = set()

        snapshot._purge([old_snap], exceptions)

        mock_ec2.delete_snapshot.assert_called_once_with(SnapshotId="snap-old")

    def test_purge_keeps_exceptions(self, mock_boto3, mocker):
        mock_ec2 = MagicMock()
        mocker.patch("staker.snapshot.boto3.client", return_value=mock_ec2)
        mocker.patch("staker.snapshot.MAX_SNAPSHOT_DAYS", 30)

        snapshot = Snapshot()
        old_snap = {
            "SnapshotId": "snap-protected",
            "StartTime": datetime.now(UTC) - timedelta(days=100),
        }
        exceptions = {"snap-protected"}

        snapshot._purge([old_snap], exceptions)

        mock_ec2.delete_snapshot.assert_not_called()

    def test_create_makes_snapshot_when_all_old(self, mock_boto3, mocker):
        """Test _create creates snapshot when all existing are old."""
        snapshot = Snapshot()
        mocker.patch.object(snapshot, "is_older_than", return_value=True)
        mocker.patch.object(snapshot, "force_create", return_value={"SnapshotId": "new"})
        mocker.patch.object(snapshot, "_put_param")

        result = snapshot._create([{"SnapshotId": "old"}])

        assert result["SnapshotId"] == "new"
        snapshot.force_create.assert_called_once()

    def test_create_skips_if_recent_exists(self, mock_boto3, mocker):
        """Test _create skips if a recent snapshot exists."""
        snapshot = Snapshot()
        mocker.patch.object(snapshot, "is_older_than", side_effect=[True, False])

        result = snapshot._create([{"SnapshotId": "old"}, {"SnapshotId": "recent"}])

        assert result is None

    def test_update_returns_true_when_refresh_needed(self, mock_boto3, mocker):
        """Test update method returning True when refresh is needed."""
        snapshot = Snapshot()
        mocker.patch.object(
            snapshot,
            "_get_snapshots",
            return_value=[{"SnapshotId": "snap-new", "StartTime": datetime.now(UTC)}],
        )
        mocker.patch.object(snapshot, "_get_param", return_value="snap-old")
        mocker.patch.object(snapshot, "_put_param")

        snapshot.ec2.describe_launch_template_versions.return_value = {
            "LaunchTemplateVersions": [
                {
                    "VersionNumber": 1,
                    "LaunchTemplateData": {
                        "BlockDeviceMappings": [
                            {"DeviceName": "/dev/sdx", "Ebs": {"SnapshotId": "snap-old"}}
                        ]
                    },
                }
            ]
        }
        snapshot.ec2.create_launch_template_version.return_value = {
            "LaunchTemplateVersion": {"VersionNumber": 2}
        }
        snapshot.auto.describe_auto_scaling_groups.return_value = {
            "AutoScalingGroups": [
                {
                    "LaunchTemplate": {"Version": "1"},
                    "Instances": [{"InstanceId": "", "LaunchTemplate": {"Version": "1"}}],
                }
            ]
        }

        result = snapshot.update()

        assert result is True

    def test_instance_is_draining_returns_true(self, mock_boto3, mocker):
        """Test instance_is_draining returns True when draining."""
        snapshot = Snapshot()
        snapshot.instance_id = "i-123"

        snapshot.ecs.list_container_instances.return_value = {"containerInstanceArns": ["arn:1"]}
        snapshot.ecs.describe_container_instances.return_value = {
            "containerInstances": [{"ec2InstanceId": "i-123", "status": "DRAINING"}]
        }

        assert snapshot.instance_is_draining() is True

    def test_backup_creates_and_purges(self, mock_boto3, mocker):
        """Test backup method flow."""
        snapshot = Snapshot()
        mocker.patch.object(snapshot, "_get_snapshots", return_value=[])
        mocker.patch.object(snapshot, "_get_exceptions", return_value=set())
        mocker.patch.object(snapshot, "_create", return_value={"SnapshotId": "new"})
        mocker.patch.object(snapshot, "_purge")

        result = snapshot.backup()

        assert result["SnapshotId"] == "new"
        snapshot._purge.assert_called_once()

    def test_terminate_calls_ec2(self, mock_boto3, mocker):
        """Test terminate calls EC2 terminate_instances."""
        snapshot = Snapshot()
        snapshot.instance_id = "i-abc"

        snapshot.terminate()

        snapshot.ec2.terminate_instances.assert_called_once_with(InstanceIds=["i-abc"])

    def test_get_exceptions_returns_ids(self, mock_boto3, mocker):
        """Test _get_exceptions returns protected snapshot IDs."""
        snapshot = Snapshot()
        mocker.patch.object(snapshot, "_get_param", return_value="snap-param")
        mocker.patch.object(snapshot, "_get_curr_snapshot_id", return_value="snap-current")

        exceptions = snapshot._get_exceptions()

        assert "snap-param" in exceptions
        assert "snap-current" in exceptions
        assert len(exceptions) == 2

    def test_get_exceptions_filters_none(self, mock_boto3, mocker):
        """Test _get_exceptions filters out None values."""
        snapshot = Snapshot()
        mocker.patch.object(snapshot, "_get_param", return_value=None)
        mocker.patch.object(snapshot, "_get_curr_snapshot_id", return_value="snap-current")

        exceptions = snapshot._get_exceptions()

        assert None not in exceptions
        assert len(exceptions) == 1

    def test_get_curr_snapshot_id_returns_id(self, mock_boto3, mocker):
        """Test _get_curr_snapshot_id extracts snapshot ID."""
        snapshot = Snapshot()
        snapshot.instance_id = "i-123"

        mocker.patch("staker.snapshot.AWS", True)
        snapshot.ec2.get_launch_template_data.return_value = {
            "LaunchTemplateData": {
                "BlockDeviceMappings": [
                    {"DeviceName": "/dev/sda", "Ebs": {}},
                    {"DeviceName": "/dev/sdx", "Ebs": {"SnapshotId": "snap-xyz"}},
                ]
            }
        }

        result = snapshot._get_curr_snapshot_id()

        assert result == "snap-xyz"

    def test_get_curr_snapshot_id_returns_none_on_error(self, mock_boto3, mocker):
        """Test _get_curr_snapshot_id returns None on error."""
        snapshot = Snapshot()

        mocker.patch("staker.snapshot.AWS", True)
        snapshot.ec2.get_launch_template_data.side_effect = ClientError(
            {"Error": {"Code": "InvalidInstance", "Message": "API error"}}, "GetLaunchTemplateData"
        )

        result = snapshot._get_curr_snapshot_id()

        assert result is None
