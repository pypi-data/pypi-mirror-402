"""MEV-Boost relay management for the Ethereum staking node.

This module handles the selection of reliable MEV relays by testing their
response times and filtering out unreliable ones.
"""

from statistics import mean, stdev
from time import sleep, time

import requests

from staker.config import RELAYS


class Booster:
    """Manages MEV relay selection and health checking.

    This class tests MEV relays for reliability and filters out those
    with poor response times or connectivity issues.
    """

    def get_relays(self) -> list[str]:
        """Determine which MEV relays are reliable.

        Tests each relay multiple times for response time and availability.
        Filters out relays that fail to respond or have inconsistent latency.

        Returns:
            List of relay URLs that passed the reliability tests.
        """
        print("Determining reliable relays...")
        relays: dict[str, float] = dict.fromkeys(RELAYS, 0)
        bad_relays: set[str] = set()
        num_trials = 5

        for _ in range(num_trials):
            for relay in RELAYS:
                if relay in bad_relays:
                    continue
                pong = self.ping(relay)
                if pong:
                    relays[relay] += pong / num_trials
                else:
                    bad_relays.add(relay)
            sleep(1)

        for relay in bad_relays:
            print(f"Invalid relay: {relay}")
            del relays[relay]

        ping_times = list(relays.values())
        if len(ping_times) < 2:
            print("Error in relay testing. Defaulting to using all specified relays.")
            return list(RELAYS)

        dev = stdev(ping_times)
        avg = mean(ping_times)

        valid_relays: list[str] = []
        for relay, res_time in relays.items():
            if abs(avg - res_time) < (2 * dev):
                print(f"Valid relay: {relay}")
                valid_relays.append(relay)

        return valid_relays

    def ping(self, domain: str) -> float | None:
        """Ping a relay to measure response time.

        Args:
            domain: The relay URL to ping.

        Returns:
            Response time in seconds if successful, None if the request failed.
        """
        try:
            start = time()
            response = requests.get(
                f"{domain}/relay/v1/data/bidtraces/proposer_payload_delivered",
                timeout=10,
            )
            end = time()
            if response.ok:
                return end - start
        except requests.exceptions.RequestException:
            pass
        return None
