# syntax=docker/dockerfile:1.9x
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.7.19 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=never


ENV workdir=/app
WORKDIR $workdir
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
RUN curl -Lo /bin/goose https://github.com/pressly/goose/releases/download/v3.24.1/goose_linux_x86_64; \
     chmod +x /bin/goose;

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends openssl ca-certificates libffi-dev build-essential libssl-dev git && \
    rm -rf /var/lib/apt/lists/*
RUN uv venv
COPY uv.lock $workdir
COPY pyproject.toml $workdir
RUN uv sync --locked --no-install-project --no-dev --compile-bytecode

RUN rm -rf /root/.cargo
# COPY code later in the layers (after dependencies are installed)
# It builds the containers 2x faster on code change
COPY . $workdir
# Most of dependencies are already installed, it only install the app
RUN uv sync --locked --no-dev --compile-bytecode  --no-editable
# RUN apt-get remove --purge -y libffi-dev build-essential libssl-dev git

FROM python:3.12-slim
ENV workdir=/app
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_NO_SYNC=1
WORKDIR $workdir
RUN mkdir -p /usr/share/fonts/truetype/dejavu
COPY DejaVuSans.ttf /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
COPY --from=build /app /app
COPY --from=build /bin/goose /usr/bin/goose
# RUN uv sync --locked --no-dev --compile-bytecode  --no-editable
