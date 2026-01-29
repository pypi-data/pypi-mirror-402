#!/bin/bash

set -eu

# Source configurations
source config.env
source versions.env

docker build \
    -t ethereum \
    --network=host \
    --build-arg DEPLOY_ENV=prod \
    --build-arg ARCH=amd64 \
    --build-arg VPN=true \
    --build-arg GETH_VERSION="${GETH_VERSION}" \
    --build-arg GETH_COMMIT="${GETH_COMMIT}" \
    --build-arg PRYSM_VERSION="${PRYSM_VERSION}" \
    --build-arg MEVBOOST_VERSION="${MEVBOOST_VERSION}" \
    .
