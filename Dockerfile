FROM python:3.12-slim AS build
ENV workdir=/app
RUN mkdir -p $workdir
WORKDIR $workdir
RUN apt-get update -y
RUN apt-get install -y openssl ca-certificates
RUN apt-get install -y libffi-dev build-essential libssl-dev git rustc cargo libpq-dev gcc curl
RUN mkdir -p bin; curl -Lo bin/goose https://github.com/pressly/goose/releases/download/v3.24.1/goose_linux_x86_64; \
     chmod +x bin/goose;
RUN pip install pip -U
RUN pip install poetry -U
COPY poetry.lock $workdir
COPY pyproject.toml $workdir
RUN poetry install --no-root --only=main

RUN rm -rf /root/.cargo
# COPY code later in the layers (after dependencies are installed)
# It builds the containers 2x faster on code change
COPY . $workdir
# Most of dependencies are already installed, it only install the app
RUN poetry install --only=main
RUN apt-get remove --purge -y libffi-dev build-essential libssl-dev git rustc cargo

ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
