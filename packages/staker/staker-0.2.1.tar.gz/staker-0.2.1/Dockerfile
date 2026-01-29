# syntax=docker/dockerfile:1

# =============================================================================
# BASE STAGE - Common setup for all stages
# =============================================================================
FROM ubuntu:24.04 AS base

# Configure home dir
ENV HOME="/root"

# Configure env vars
ARG DEPLOY_ENV
ARG VERSION
ARG ARCH
ARG VPN
ENV DEPLOY_ENV="${DEPLOY_ENV:-prod}"
ENV VERSION="${VERSION}"
ENV ARCH="${ARCH:-arm64}"
ENV VPN="${VPN:-false}"
ENV ETH_DIR="${HOME}/ethereum"
ENV EXEC_DIR="${ETH_DIR}/execution"
ENV MEV_DIR_BASE="/mev"
ENV MEV_DIR="${ETH_DIR}${MEV_DIR_BASE}"
ENV PRYSM_DIR_BASE="/consensus/prysm"
ENV PRYSM_DIR="${ETH_DIR}${PRYSM_DIR_BASE}"

# Install deps and uv in single layer
RUN apt-get update && \
    apt-get install -y python3 git curl bash make && \
    rm -rf /var/lib/apt/lists/* && \
    curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="${HOME}/.local/bin:${PATH}"

WORKDIR "${ETH_DIR}"

# =============================================================================
# TEST STAGE - Run lint and coverage checks
# =============================================================================
FROM base AS test

# Copy project files needed for testing
COPY pyproject.toml uv.lock README.md Makefile ./
COPY src/ src/
COPY tests/ tests/

# Install dependencies and run checks in single layer
RUN make ci && make lint && make cov && touch /tmp/.tests_passed

# =============================================================================
# DEPLOY STAGE - Runtime image (can be targeted directly to skip tests)
# =============================================================================
FROM base AS deploy

# Install Python dependencies (runtime only for binary downloads)
COPY pyproject.toml uv.lock README.md Makefile ./
RUN make ci DEPLOY=1

# Download geth (execution) - single layer to avoid orphaned archives
ARG GETH_VERSION
ARG GETH_COMMIT
ENV PLATFORM_ARCH="linux-${ARCH}"
ENV GETH_ARCHIVE="geth-${PLATFORM_ARCH}-${GETH_VERSION}-${GETH_COMMIT}"
RUN mkdir -p "${EXEC_DIR}" && \
    cd "${EXEC_DIR}" && \
    curl -LO "https://gethstore.blob.core.windows.net/builds/${GETH_ARCHIVE}.tar.gz" && \
    tar -xvzf "${GETH_ARCHIVE}.tar.gz" && \
    mv "${GETH_ARCHIVE}/geth" . && \
    rm -rf "${GETH_ARCHIVE}" "${GETH_ARCHIVE}.tar.gz" && \
    chmod +x geth
ENV PATH="${PATH}:${EXEC_DIR}"

# Download prysm (consensus)
ARG PRYSM_VERSION
RUN mkdir -p "${PRYSM_DIR}" && \
    cd "${PRYSM_DIR}" && \
    export PRYSM_PLATFORM_ARCH="${PLATFORM_ARCH}" && \
    if [ "$ARCH" = "amd64" ]; then export PRYSM_PLATFORM_ARCH="modern-${PLATFORM_ARCH}"; fi && \
    curl -Lo beacon-chain "https://github.com/prysmaticlabs/prysm/releases/download/v${PRYSM_VERSION}/beacon-chain-v${PRYSM_VERSION}-${PRYSM_PLATFORM_ARCH}" && \
    curl -Lo validator "https://github.com/prysmaticlabs/prysm/releases/download/v${PRYSM_VERSION}/validator-v${PRYSM_VERSION}-${PLATFORM_ARCH}" && \
    curl -Lo prysmctl "https://github.com/prysmaticlabs/prysm/releases/download/v${PRYSM_VERSION}/prysmctl-v${PRYSM_VERSION}-${PLATFORM_ARCH}" && \
    chmod +x beacon-chain validator prysmctl
ENV PATH="${PATH}:${PRYSM_DIR}"

# Download mev-boost
ARG MEVBOOST_VERSION
ENV MEV_ARCHIVE="mev-boost_${MEVBOOST_VERSION}_linux_${ARCH}"
RUN mkdir -p "${MEV_DIR}" && \
    cd "${MEV_DIR}" && \
    curl -LO "https://github.com/flashbots/mev-boost/releases/download/v${MEVBOOST_VERSION}/${MEV_ARCHIVE}.tar.gz" && \
    tar -xvzf "${MEV_ARCHIVE}.tar.gz" && \
    rm -f "${MEV_ARCHIVE}.tar.gz" LICENSE README.md && \
    chmod +x mev-boost
ENV PATH="${PATH}:${MEV_DIR}"

# Setup VPN configs (if VPN=true)
# Install build deps, run setup, clean up - all in one layer to avoid bloat
WORKDIR "${ETH_DIR}"
COPY vpn vpn
RUN if [ "${VPN}" = "true" ]; then \
        make ci && \
        bash vpn/setup.sh && \
        make ci DEPLOY=1; \
    fi

COPY src/staker src/staker
ENV PYTHONPATH="${ETH_DIR}/src"
EXPOSE 30303/tcp 30303/udp 13000/tcp 12000/udp
ENTRYPOINT ["python3", "-m", "staker.node"]

# =============================================================================
# DEFAULT STAGE - Ensures tests pass before deploy
# =============================================================================
FROM deploy AS default

# This COPY creates a dependency on the test stage
# Build will fail if tests didn't pass
COPY --from=test /tmp/.tests_passed /tmp/.tests_passed
