.PHONY: format format-test check fix clean clean-build clean-pyc clean-test coverage install pylint pylint-quick pyre test publish uv-check publish isort isort-check docker-push docker-build migrate

APP_ENV ?= dev
VERSION := `cat VERSION`
package := antgent
NAMESPACE := antgent

DOCKER_BUILD_ARGS ?= "-q"

all: fix


help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "dist - package"
	@echo "install - install the package to the active Python's site-packages"
	@echo "migrate - Execute a db migration"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -not -path ".venv/*" -not -path ".cache/*" -prune  -name '*.egg-info' -exec rm -fr {} +
	find . -not -path ".venv/*" -not -path ".cache/*" -prune -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -type d \( -path './.venv' -o -path './.cache' \) -prune -o -name '*.egg-info' -exec rm -rf {} +
	find . -type d \( -path './.venv' -o -path './.cache' \) -prune -o -name '*.egg' -exec rm -f {} +
	find . -type d \( -path './.venv' -o -path './.cache' \) -prune -o -name '*.pyc' -exec rm -f {} +
	find . -type d \( -path './.venv' -o -path './.cache' \) -prune -o -name '*.pyo' -exec rm -f {} +
	find . -type d \( -path './.venv' -o -path './.cache' \) -prune -o -name '*~' -exec rm -f {} +
	find . -type d \( -path './.venv' -o -path './.cache' \) -prune -o -name 'flycheck_*' -exec rm -f {} +
	find . -type d \( -path './.venv' -o -path './.cache' \) -prune -o -name '__pycache__' -exec rm -rf {} +
	find . -type d \( -path './.venv' -o -path './.cache' \) -prune -o -name '.mypy_cache' -exec rm -rf {} +
	find . -type d \( -path './.venv' -o -path './.cache' \) -prune -o -name '.pyre' -exec rm -rf {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -f coverage.xml
	rm -f report.xml
test:
	ANTGENT_CONFIG=tests/data/test_config.yaml uv run py.test --cov=$(package) --verbose tests --cov-report=html --cov-report=term --cov-report xml:coverage.xml --cov-report=term-missing --junitxml=report.xml --asyncio-mode=auto

coverage:
	uv run coverage run --source $(package) setup.py test
	uv run coverage report -m
	uv run coverage html
	$(BROWSER) htmlcov/index.html

install: clean
	uv install

pylint-quick:
	uv run pylint --rcfile=.pylintrc $(package)  -E -r y

pylint:
	uv run pylint --rcfile=".pylintrc" $(package)
pyright:
	uv run pyright

lint: format-test isort-check ruff uv-check
small-check: format-test isort-check uv-check
check: lint pyright

pyre: pyre-check

pyre-check:
	uv run pyre --noninteractive check 2>/dev/null

format:
	uv run ruff format $(package)

format-test:
	uv run ruff format $(package) --check

uv-check:
	uv lock --locked --offline

publish: clean
	uv build
	uv publish

isort:
	uv run ruff check --select I $(package) tests --fix

isort-check:
	uv run ruff check --select I $(package) tests

ruff:
	uv run ruff check

fix: format isort
	uv run ruff check --fix --unsafe-fixes

.ONESHELL:
pyrightconfig:
	jq \
      --null-input \
      --arg venv "$$(basename $$(uv env info -p))" \
      --arg venvPath "$$(dirname $$(uv env info -p))" \
      '{ "venv": $$venv, "venvPath": $$venvPath }' \
      > pyrightconfig.json

rename:
	ack antgent -l | xargs -i{} sed -r -i "s/antgent/antgent/g" {}
	ack Antgent -i -l | xargs -i{} sed -r -i "s/Antgent/Antgent/g" {}
	ack ANTGENT -i -l | xargs -i{} sed -r -i "s/ANTGENT/ANTGENT/g" {}

run-worker:
	uv run bin/antgent  looper --namespace default  --host 127.0.0.1:7233 --config=localconfig.yaml

run-server:
	./bin/antgent server --config localconfig.yaml

temporal-init-namespace:
	temporal operator namespace  create -n antgent-dev-al --retention 72h0m0s --description "antgent stg namespace"

ipython:
	uv run ipython

temporal-schedule:
	uv run bin/antgent scheduler --namespace default  --host 127.0.0.1:7233  --config=localconfig.yaml -s scheduly.yaml

CONTAINER_REGISTRY=ghcr.io/ant31/$(package)

docker-push-local: docker-build-locall
    docker push $(CONTAINER_REGISTRY):latest

docker-build-local:
    docker build --network=host -t $(CONTAINER_REGISTRY):latest .

docker-push:
	docker buildx build --push -t $(CONTAINER_REGISTRY):latest .

BUMP ?= patch
bump:
	uv run bump-my-version bump $(BUMP)

upgrade-dep:
	uv sync --upgrade
	uv lock -U --resolution=highest

docs:
	uv run mkdocs build

serve-docs:
	uv run mkdocs serve
