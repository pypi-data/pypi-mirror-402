#!/bin/bash

set -eu
source config.env


VPN="${VPN:-true}"

docker run \
    --env ETH_ADDR="${ETH_ADDR}" \
    --env AWS_DEFAULT_REGION=us-east-1 \
    --env DOCKER=true \
    --env VPN_USER="${VPN_USER}" \
    --env VPN_PASS="${VPN_PASS}" \
    --env VPN="${VPN}" \
    --cap-add=NET_ADMIN \
    --device=/dev/net/tun \
    -p 30303:30303/tcp \
    -p 30303:30303/udp \
    -p 13000:13000/tcp \
    -p 12000:12000/udp \
    -v ~:/mnt/ebs \
    --dns 8.8.8.8 \
    --name ethereum \
    --rm \
    --tty \
  ethereum
