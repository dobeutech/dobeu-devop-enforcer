FROM mcr.microsoft.com/devcontainers/base:2.0.4-noble

RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
        bubblewrap \
        curl \
        jq \
        python3 \
        python3-jsonschema \
        shellcheck \
    && chmod 4755 /usr/bin/bwrap \
    && rm -rf /var/lib/apt/lists/*
