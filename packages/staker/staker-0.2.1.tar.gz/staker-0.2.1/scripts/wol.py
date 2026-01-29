"""Wake-on-LAN utility for the Ethereum staking server."""

import os

from dotenv import find_dotenv, load_dotenv
from wakeonlan import send_magic_packet

load_dotenv(find_dotenv("config.env"))

send_magic_packet(os.environ["MAC_ADDR"], ip_address="eth.machine.one")
