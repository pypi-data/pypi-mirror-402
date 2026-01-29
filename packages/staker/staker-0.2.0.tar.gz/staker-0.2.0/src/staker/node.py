"""Ethereum staking node orchestrator.

This module provides the main Node class that orchestrates the execution,
consensus, validation, and MEV-boost processes for an Ethereum staking node.
"""

from __future__ import annotations

import logging
import os
import select
import signal
import subprocess
import sys
import tempfile
from glob import glob
from random import choice
from time import sleep, time
from typing import IO

from rich.console import Console

from staker.config import (
    AWS,
    DEV,
    DOCKER,
    ETH_ADDR,
    KILL_TIME,
    SNAPSHOT_DAYS,
    VPN,
    VPN_TIMEOUT,
)
from staker.environment import AWSEnvironment, Environment, LocalEnvironment
from staker.mev import Booster
from staker.snapshot import NoOpSnapshotManager, Snapshot, SnapshotManager
from staker.utils import colorize_log, get_checkpoint, get_checkpoint_url, get_public_ip

home_dir = os.path.expanduser("~")
platform = sys.platform.lower()
console = Console(highlight=False)
print = console.print


class Node:
    """Ethereum staking node orchestrator.

    Manages the lifecycle of Geth (execution), Prysm (consensus/validation),
    and MEV-Boost processes, including VPN connection handling, graceful
    shutdown, and optional snapshot management on AWS.

    Attributes:
        env: The runtime environment (AWS or Local).
        snapshot: The snapshot manager for EBS backups.
        booster: The MEV relay selector.
    """

    def __init__(
        self,
        env: Environment,
        snapshot: SnapshotManager,
        booster: Booster | None = None,
    ) -> None:
        """Initialize the Node with injected dependencies.

        Args:
            env: Runtime environment abstraction.
            snapshot: Snapshot manager for backups.
            booster: MEV relay selector (created if not provided).
        """
        self.env = env
        self.snapshot = snapshot
        self.booster = booster or Booster()

        on_mac = platform == "darwin"
        prefix = env.get_data_prefix() if DOCKER else home_dir
        geth_dir_base = f"/{'Library/Ethereum' if on_mac else '.ethereum'}"
        prysm_dir_base = f"/{'Library/Eth2' if on_mac else '.eth2'}"
        prysm_wallet_postfix = f"{'V' if on_mac else 'v'}alidators/prysm-wallet-v2"
        geth_dir_postfix = "/hoodi" if DEV else ""

        self.geth_data_dir = f"{prefix}{geth_dir_base}{geth_dir_postfix}"
        self.prysm_data_dir = f"{prefix}{prysm_dir_base}"
        self.prysm_wallet_dir = f"{self.prysm_data_dir}{prysm_wallet_postfix}"

        ipc_postfix = "/geth.ipc"
        self.ipc_path = self.geth_data_dir + ipc_postfix
        self.kill_in_progress = False
        self.terminating = False
        self.processes: list[dict] = []
        self.streams: list[IO[bytes]] = []
        self.relays: list[str] = []
        self.most_recent: dict | None = None
        self.logs_file = env.get_logs_path()

        with open(self.logs_file, "w") as _:
            pass

    def _run_cmd(self, cmd: list[str]) -> subprocess.Popen:
        """Run a command and return the process handle.

        Args:
            cmd: Command and arguments to run.

        Returns:
            The subprocess.Popen handle.
        """
        print(f"Running cmd: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return process

    def _execution(self) -> subprocess.Popen:
        """Start the Geth execution client.

        Returns:
            The Geth process handle.
        """
        args = [
            "--http",
            "--http.api",
            "eth,net,engine,admin",
            "--state.scheme=path",
        ]

        if DEV:
            args.append("--hoodi")
        else:
            args.append("--mainnet")

        if DOCKER:
            args.append(f"--datadir={self.geth_data_dir}")

        cmd = ["geth"] + args
        return self._run_cmd(cmd)

    def _consensus(self) -> subprocess.Popen:
        """Start the Prysm beacon chain.

        Returns:
            The beacon-chain process handle.
        """
        args = [
            "--accept-terms-of-use",
            f"--execution-endpoint={self.ipc_path}",
            f"--suggested-fee-recipient={ETH_ADDR}",
            "--blob-storage-layout=by-epoch",
            "--http-mev-relay=http://localhost:18550",
            "--enable-backfill",
        ]

        # Network-specific configuration
        network = "hoodi" if DEV else "mainnet"
        args.append(f"--{network}")

        # ChainSafe checkpoint sync (strongly recommended with weak subjectivity checkpoint)
        checkpoint_url = get_checkpoint_url(network)
        args.append(f"--checkpoint-sync-url={checkpoint_url}")
        args.append(f"--genesis-beacon-api-url={checkpoint_url}")

        # Try to fetch weak subjectivity checkpoint, but don't fail if unavailable
        try:
            checkpoint = get_checkpoint(network)
            args.append(f"--weak-subjectivity-checkpoint={checkpoint}")
        except Exception as e:
            print(
                f"[bright_yellow]WARNING: Failed to fetch weak subjectivity checkpoint: {e}[/bright_yellow]"
            )

        if DOCKER:
            args.append(f"--datadir={self.prysm_data_dir}")

        p2p_host = self.env.get_p2p_host_dns(DEV)
        if p2p_host:
            args.append(f"--p2p-host-dns={p2p_host}")

        cmd = ["beacon-chain"] + args
        return self._run_cmd(cmd)

    def _validation(self) -> subprocess.Popen:
        """Start the Prysm validator client.

        Returns:
            The validator process handle.
        """
        args = [
            "--accept-terms-of-use",
            "--enable-builder",
            f"--wallet-dir={self.prysm_wallet_dir}",
            f"--suggested-fee-recipient={ETH_ADDR}",
            f"--wallet-password-file={self.prysm_wallet_dir}/password.txt",
        ]

        if DEV:
            args.append("--hoodi")
        else:
            args.append("--mainnet")

        cmd = ["validator"] + args
        return self._run_cmd(cmd)

    def _mev(self) -> subprocess.Popen:
        """Start the MEV-Boost relay.

        Returns:
            The mev-boost process handle.
        """
        args = ["-relay-check"]
        if DEV:
            args.append("-hoodi")
        else:
            args.append("-mainnet")

        args += ["-relays", ",".join(self.relays)]
        cmd = ["mev-boost"] + args
        return self._run_cmd(cmd)

    def _vpn(self) -> tuple[subprocess.Popen, str]:
        """Start the OpenVPN client.

        Creates a secure temp file for credentials with restrictive permissions.

        Returns:
            Tuple of (openvpn process handle, path to credentials file).
        """
        vpn_user = os.environ["VPN_USER"]
        vpn_pass = os.environ["VPN_PASS"]

        # Create temp file with 0600 permissions (owner read/write only)
        fd, creds_path = tempfile.mkstemp(prefix="vpn_creds_", text=True)
        os.chmod(creds_path, 0o600)
        with os.fdopen(fd, "w") as file:
            file.write(f"{vpn_user}\n{vpn_pass}")

        cfg = choice(glob("config/us*.tcp.ovpn"))
        args = ["--config", cfg, "--auth-user-pass", creds_path]
        cmd = ["openvpn"] + args
        return self._run_cmd(cmd), creds_path

    def _cleanup_creds(self, path: str | None) -> None:
        """Remove credentials file if it exists.

        Args:
            path: Path to the credentials file, or None.
        """
        if path and os.path.exists(path):
            os.unlink(path)

    def _wait_for_vpn(self) -> list[dict]:
        """Wait for VPN connection with timeout and retry.

        Attempts to connect to VPN, retrying indefinitely if the connection
        times out after VPN_TIMEOUT seconds.

        Returns:
            List containing the VPN process metadata.
        """
        processes: list[dict] = []
        start_ip = get_public_ip()
        vpn_connected = False
        creds_path = None

        while not vpn_connected:
            vpn_process, creds_path = self._vpn()
            processes.append({"process": vpn_process, "prefix": "xxx OPENVPN__ xxx"})
            elapsed = 0

            while start_ip == get_public_ip() and elapsed < VPN_TIMEOUT:
                print("Waiting for VPN...")
                sleep(VPN_TIMEOUT / 3)
                elapsed += VPN_TIMEOUT / 3

            if start_ip == get_public_ip():
                print(f"VPN connection timed out after {VPN_TIMEOUT}s, retrying...")
                os.kill(vpn_process.pid, signal.SIGKILL)
                processes.pop()
                self._cleanup_creds(creds_path)
            else:
                vpn_connected = True

        # Clean up creds file after VPN connects (OpenVPN has already read it)
        self._cleanup_creds(creds_path)

        return processes

    def _start(self) -> tuple[list[dict], list[IO[bytes]]]:
        """Start all node processes.

        Optionally connects to VPN first, then starts execution, consensus,
        validation, and MEV-boost processes.

        Returns:
            Tuple of (processes list, stdout streams list).
        """
        processes: list[dict] = []

        if VPN:
            processes = self._wait_for_vpn()

        processes += [
            {"process": self._execution(), "prefix": "<<< EXECUTION >>>"},
            {"process": self._consensus(), "prefix": "[[[ CONSENSUS ]]]"},
            {"process": self._validation(), "prefix": "(( _VALIDATION ))"},
            {"process": self._mev(), "prefix": "+++ MEV_BOOST +++"},
        ]

        streams: list[IO[bytes]] = []
        for meta in processes:
            meta["process"].stdout.prefix = meta["prefix"]
            streams.append(meta["process"].stdout)

        self.processes = processes
        self.streams = streams
        return processes, streams

    def _signal_processes(self, sig: signal.Signals, prefix: str, hard: bool = True) -> None:
        """Send a signal to all managed processes.

        Args:
            sig: The signal to send.
            prefix: Log message prefix.
            hard: If False and kill_in_progress, skip signaling.
        """
        if hard or not self.kill_in_progress:
            print(f"{prefix} all processes... [{'HARD' if hard else 'SOFT'}]")
            for meta in self.processes:
                try:
                    os.kill(meta["process"].pid, sig)
                except OSError as e:
                    logging.exception(e)

    def _interrupt(self, **kwargs) -> None:
        """Send SIGINT to all processes."""
        self._signal_processes(signal.SIGINT, "Interrupting", **kwargs)

    def _terminate(self, **kwargs) -> None:
        """Send SIGTERM to all processes."""
        self._signal_processes(signal.SIGTERM, "Terminating", **kwargs)

    def _kill(self, **kwargs) -> None:
        """Send SIGKILL to all processes."""
        self._signal_processes(signal.SIGKILL, "Killing", **kwargs)

    def _print_line(self, prefix: str, line: bytes) -> str | None:
        """Print and log a line of process output.

        Args:
            prefix: The process prefix for the log line.
            line: The raw output bytes.

        Returns:
            The formatted log line, or None if empty.
        """
        decoded = line.decode("UTF-8").strip()
        if decoded:
            log = f"{prefix} {decoded}"
            colored = colorize_log(log)
            print(colored if self.env.use_colored_logs() else log)
            with open(self.logs_file, "a") as file:
                file.write(f"{log}\n")
            return log
        return None

    def _stream_logs(self, rstreams: list[IO[bytes]]) -> list[str | None]:
        """Read and print available log lines from streams.

        Args:
            rstreams: List of ready streams to read from.

        Returns:
            List of formatted log lines.
        """
        return [self._print_line(stream.prefix, stream.readline()) for stream in rstreams]

    def _squeeze_logs(self, processes: list[dict]) -> None:
        """Drain remaining output from all processes.

        Args:
            processes: List of process metadata dicts.
        """
        for meta in processes:
            stream = meta["process"].stdout
            for line in iter(stream.readline, b""):
                self._print_line(stream.prefix, line)

    def _interrupt_on_error(self, logs: list[str | None]) -> bool:
        """Check for known error conditions and interrupt if found.

        Args:
            logs: List of log lines to check.

        Returns:
            True if an error was detected and interrupt sent.
        """
        for log in logs:
            if log and "Beacon backfilling failed" in log:
                self._interrupt(hard=False)
                return True
        return False

    def _poll_processes(self, processes: list[dict]):
        """Generate poll results for all processes.

        Args:
            processes: List of process metadata dicts.

        Yields:
            True for each dead process, False for running.
        """
        return (meta["process"].poll() is not None for meta in processes)

    def _all_processes_are_dead(self, processes: list[dict]) -> bool:
        """Check if all processes have terminated.

        Args:
            processes: List of process metadata dicts.

        Returns:
            True if all processes are dead.
        """
        return all(self._poll_processes(processes))

    def _any_process_is_dead(self, processes: list[dict]) -> bool:
        """Check if any process has terminated.

        Args:
            processes: List of process metadata dicts.

        Returns:
            True if any process is dead.
        """
        return any(self._poll_processes(processes))

    def _handle_gracefully(self, processes: list[dict], hard: bool) -> None:
        """Gracefully stop all processes with escalating signals.

        Sends SIGINT, waits for KILL_TIME, escalates to SIGTERM,
        waits again, then SIGKILL if needed.

        Args:
            processes: List of process metadata dicts.
            hard: Whether this is a hard stop (ignores kill_in_progress).
        """

        def wait_for_exit() -> bool:
            start = time()
            while not self._all_processes_are_dead(processes) and time() - start < KILL_TIME:
                sleep(1)
            return self._all_processes_are_dead(processes)

        # Send SIGINT first for graceful shutdown
        self._interrupt(hard=hard)
        if not wait_for_exit():
            self._terminate(hard=hard)
        if not wait_for_exit():
            self._kill(hard=hard)
        # Log rest of output
        self._squeeze_logs(self.processes)

    def run(self) -> None:
        """Run the staking node main loop.

        Manages snapshot updates, starts all processes, monitors output,
        and handles restarts when needed.
        """
        if self.env.should_manage_snapshots():
            terminate = self.snapshot.update()
            if terminate:
                self.terminating = True
                self.snapshot.terminate()
                while self.terminating:
                    print("Waiting for stale EC2 instance to terminate...")
                    sleep(5)

        while True:
            self.most_recent = self.snapshot.backup()
            self.relays = self.booster.get_relays()
            processes, streams = self._start()
            sent_interrupt = False

            while True:
                rstreams, _, _ = select.select(streams, [], [])
                backup_is_recent = not self.snapshot.is_older_than(self.most_recent, SNAPSHOT_DAYS)
                if not backup_is_recent and not sent_interrupt:
                    print("Pausing node to initiate snapshot.")
                    self._interrupt(hard=False)
                    sent_interrupt = True

                logs = self._stream_logs(rstreams)
                self._interrupt_on_error(logs)
                if self._any_process_is_dead(processes):
                    break

            self._handle_gracefully(self.processes, hard=False)

    def stop(self) -> None:
        """Stop the node gracefully and exit.

        Handles graceful shutdown, creates final snapshot if draining,
        then exits the process.
        """
        self.kill_in_progress = True
        self._handle_gracefully(self.processes, hard=True)
        print("Node stopped")
        if (
            self.env.should_manage_snapshots()
            and self.snapshot.instance_is_draining()
            and not self.terminating
        ):
            self.snapshot.force_create()
            self.snapshot.update()
        exit(0)


def main() -> None:
    """Entry point for the staking node."""
    env = AWSEnvironment() if AWS else LocalEnvironment()
    snapshot = Snapshot() if AWS else NoOpSnapshotManager()
    node = Node(env=env, snapshot=snapshot)

    def handle_signal(*_) -> None:
        node.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    node.run()


if __name__ == "__main__":
    main()

# TODO:
# - export metrics / have an easy way to monitor, Prometheus and Grafana Cloud free, node exporter
# for prod, use savings plan (strictly better alt to reserved instances)
#   - compute savings plan ec2 - r6g.xlarge $0.10 53% 3 yrs upfront / $0.14 32% 1 yr upfront
#       ∧∧∧ More flexible
#       ∨∨∨ Limited to instance family r6g - bad if using t4g, fine for either r6g or m6g
#   - ec2 instance savings pla - r6g.xlarge $0.08 62% 3 yrs upfront / $0.12 41% 1 yr upfront
# - cut max peers to save on data out costs

# Extra:
# turn off node for 10 min every 24 hrs?
# - data integrity protection
#   - shutdown / terminate instance if process fails and others continue => forces new vol
#       - perhaps implement counter so if 3 process failures in a row, terminate instance
#   - use `geth --exec '(eth?.syncing?.currentBlock/eth?.syncing?.highestBlock)*100' attach`
#       - will yield NaN if already synced or 68.512213 if syncing
# - enable swap space if need more memory w 4vCPUs
#   - disabled on host by default for ecs optimized amis
#   - also need to set swap in task def
#   - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/container-swap.html
# - use trusted nodes json
#   - perhaps this https://www.ethernodes.org/tor-seed-nodes
