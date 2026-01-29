"""Dynamic DNS updater for Route53."""

import os
from time import sleep

import boto3
import requests
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv("config.env"))

TTL = 3600

# IP check domains with failover
IP_CHECK_DOMAINS: list[str] = ["4.ident.me", "4.tnedi.me"]


def get_ip() -> str:
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


def update_ddns(ip: str) -> dict:
    """Update the Route53 A record with the current IP.

    Args:
        ip: The IP address to set.

    Returns:
        The Route53 API response.
    """
    client = boto3.client("route53")
    response = client.change_resource_record_sets(
        ChangeBatch={
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": "eth.machine.one",
                        "ResourceRecords": [
                            {
                                "Value": ip,
                            },
                        ],
                        "TTL": TTL,
                        "Type": "A",
                    },
                },
            ],
            "Comment": "DDNS",
        },
        HostedZoneId=os.environ["HOSTED_ZONE"],
    )
    return response


if __name__ == "__main__":
    while True:
        current_ip = get_ip()
        if current_ip:
            update_ddns(current_ip)
        sleep(TTL)
