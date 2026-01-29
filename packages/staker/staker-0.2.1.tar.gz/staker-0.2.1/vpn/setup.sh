#!/bin/bash

set -eu

VPN="${VPN:-false}"

if [[ "${VPN}" = "true" ]]
then
    apt-get update && apt-get install -y openvpn ca-certificates
    # Use uv run to ensure Python deps (geoip2, requests) are available
    uv run python vpn/download.py
fi
