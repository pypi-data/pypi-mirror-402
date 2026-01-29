"""Configuration constants for the Ethereum staking node.

This module defines environment variables, network settings, and MEV relay
configurations for both mainnet and Hoodi testnet.
"""

import os

# Environment configuration
DEPLOY_ENV: str = os.environ["DEPLOY_ENV"]
ETH_ADDR: str = os.environ["ETH_ADDR"]
DEV: bool = DEPLOY_ENV.lower() == "dev"

# Process management
KILL_TIME: int = 30
VPN_TIMEOUT: int = 10
MAX_PEERS: int = 10


def get_env_bool(var_name: str) -> bool:
    """Get a boolean value from an environment variable.

    Args:
        var_name: Name of the environment variable.

    Returns:
        True if the environment variable is set to 'true' (case-insensitive),
        False otherwise.
    """
    return bool(os.environ.get(var_name) and os.environ[var_name].lower() == "true")


AWS: bool = get_env_bool("AWS")
DOCKER: bool = get_env_bool("DOCKER")
VPN: bool = get_env_bool("VPN")

# Snapshot configuration
MAX_SNAPSHOTS: int = 3
SNAPSHOT_DAYS: int = 30
MAX_SNAPSHOT_DAYS: int = MAX_SNAPSHOTS * SNAPSHOT_DAYS

# Log coloring styles for Rich console
LOG_STYLES: dict[str, str] = {
    "OPENVPN": "orange",
    "EXECUTION": "bold magenta",
    "CONSENSUS": "bold cyan",
    "VALIDATION": "bold yellow",
    "MEV_BOOST": "bold green",
    "INFO": "green",
    "WARN": "bright_yellow",
    "WARNING": "bright_yellow",
    "ERROR": "bright_red",
    "level=info": "green",
    "level=warning": "bright_yellow",
    "level=error": "bright_red",
}

# MEV Relays - Mainnet (7 relays)
RELAYS_MAINNET: list[str] = [
    # Aestus
    "https://0xa15b52576bcbf1072f4a011c0f99f9fb6c66f3e1ff321f11f461d15e31b1cb359caa092c71bbded0bae5b5ea401aab7e@aestus.live",
    # Agnostic
    "https://0xa7ab7a996c8584251c8f925da3170bdfd6ebc75d50f5ddc4050a6fdc77f2a3b5fce2cc750d0865e05d7228af97d69561@agnostic-relay.net",
    # bloXroute max profit
    "https://0x8b5d2e73e2a3a55c6c87b8b6eb92e0149a125c852751db1422fa951e42a09b82c142c3ea98d0d9930b056a3bc9896b8f@bloxroute.max-profit.blxrbdn.com",
    # Flashbots
    "https://0xac6e77dfe25ecd6110b8e780608cce0dab71fdd5ebea22a16c0205200f2f8e2e3ad3b71d3499c54ad14d6c21b41a37ae@boost-relay.flashbots.net",
    # Ultra Sound
    "https://0xa1559ace749633b997cb3fdacffb890aeebdb0f5a3b6aaa7eeeaf1a38af0a8fe88b9e4b1f61f236d2e64d95733327a62@relay.ultrasound.money",
    # Wenmerge
    "https://0x8c7d33605ecef85403f8b7289c8058f440cbb6bf72b055dfe2f3e2c6695b6a1ea5a9cd0eb3a7982927a463feb4c3dae2@relay.wenmerge.com",
    # Titan
    "https://0x8c4ed5e24fe5c6ae21018437bde147693f68cda427cd1122cf20819c30eda7ed74f72dece09bb313f2a1855595ab677d@global.titanrelay.xyz",
]

# MEV Relays - Hoodi testnet (4 relays)
RELAYS_HOODI: list[str] = [
    # Flashbots
    "https://0xafa4c6985aa049fb79dd37010438cfebeb0f2bd42b115b89dd678dab0670c1de38da0c4e9138c9290a398ecd9a0b3110@boost-relay-hoodi.flashbots.net",
    # Aestus
    "https://0x98f0ef62f00780cf8eb06701a7d22725b9437d4768bb19b363e882ae87129945ec206ec2dc16933f31d983f8225772b6@hoodi.aestus.live",
    # bloXroute
    "https://0x821f2a65afb70e7f2e820a925a9b4c80a159620582c1766b1b09729fec178b11ea22abb3a51f07b288be815a1a2ff516@bloxroute.hoodi.blxrbdn.com",
    # Titan
    "https://0xaa58208899c6105603b74396734a6263cc7d947f444f396a90f7b7d3e65d102aec7e5e5291b27e08d02c50a050825c2f@hoodi.titanrelay.xyz",
]

# Select relays based on environment
RELAYS: list[str] = RELAYS_HOODI if DEV else RELAYS_MAINNET
