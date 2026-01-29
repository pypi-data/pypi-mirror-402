"""Utility functions for the Ethereum staking node."""

import requests

from staker.config import LOG_STYLES

# IP check domains with failover
IP_CHECK_DOMAINS: list[str] = ["4.ident.me", "4.tnedi.me"]


def get_public_ip() -> str:
    """Get the current public IP address with failover between domains.

    Tries each domain in IP_CHECK_DOMAINS, rotating on failure until
    one succeeds. Logs failures to console.

    Returns:
        The public IP address as a string.
    """
    domain_idx = 0
    while True:
        domain = IP_CHECK_DOMAINS[domain_idx]
        try:
            return requests.get(f"https://{domain}", timeout=5).text
        except requests.exceptions.RequestException as e:
            print(f"Failed to reach {domain}: {e}, trying alternate...")
            domain_idx = (domain_idx + 1) % len(IP_CHECK_DOMAINS)


def colorize_log(text: str) -> str:
    """Apply Rich console color styles to log text.

    Replaces keywords in the text with Rich markup for colored output.

    Args:
        text: The log line to colorize.

    Returns:
        The text with Rich color markup applied.
    """
    for key, style in LOG_STYLES.items():
        text = text.replace(key, f"[{style}]{key}[/{style}]")
    return text


def get_checkpoint_url(network: str) -> str:
    """Get the ChainSafe checkpoint sync URL for a network.

    Args:
        network: Network name ('hoodi' or 'mainnet').

    Returns:
        The ChainSafe beacon state URL for the network.
    """
    return f"https://beaconstate-{network}.chainsafe.io"


def get_checkpoint(network: str) -> str:
    """Fetch the current weak subjectivity checkpoint from ChainSafe.

    Args:
        network: Network name ('hoodi' or 'mainnet').

    Returns:
        Checkpoint in block_root:epoch format.
    """
    url = f"{get_checkpoint_url(network)}/eth/v1/beacon/states/finalized/finality_checkpoints"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    finalized = data["data"]["finalized"]
    return f"{finalized['root']}:{finalized['epoch']}"
