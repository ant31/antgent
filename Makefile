.PHONY: format format-test check fix clean clean-build clean-pyc clean-test coverage install pylint pylint-quick pyre test publish poetry-check publish isort isort-check docker-push docker-build migrate

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
	find . -not -path ".venv/*" -not -path ".cache/*" -prune -name '*.pyc' -exec rm -f {} +
	find . -not -path ".venv/*" -not -path ".cache/*" -prune -name '*.pyo' -exec rm -f {} +
	find . -not -path ".venv/*" -not -path ".cache/*" -prune -name '*~' -exec rm -f {} +
	find . -not -path ".venv/*" -not -path ".cache/*" -prune -name 'flycheck_*' -exec rm -f {} +
	find . -not -path ".venv/*" -not -path ".cache/*" -prune -name '__pycache__' -exec rm -fr {} +
	find . -not -path ".venv/*" -not -path ".cache/*" -prune -name '.mypy_cache' -exec rm -fr {} +
	find . -not -path ".venv/*" -not -path ".cache/*" -prune -name '.pyre' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -f coverage.xml
	rm -f report.xml
test:
	ANTGENT_CONFIG=tests/data/test_config.yaml poetry run py.test --cov=$(package) --verbose tests --cov-report=html --cov-report=term --cov-report xml:coverage.xml --cov-report=term-missing --junitxml=report.xml --asyncio-mode=auto

coverage:
	poetry run coverage run --source $(package) setup.py test
	poetry run coverage report -m
	poetry run coverage html
	$(BROWSER) htmlcov/index.html

install: clean
	poetry install

pylint-quick:
	poetry run pylint --rcfile=.pylintrc $(package)  -E -r y

pylint:
	poetry run pylint --rcfile=".pylintrc" $(package)

check: format-test isort-check ruff poetry-check

pyre: pyre-check

pyre-check:
	poetry run pyre --noninteractive check 2>/dev/null

format:
	poetry run ruff format $(package)

format-test:
	poetry run ruff format $(package) --check

poetry-check:
	poetry check --lock

publish: clean
	poetry build
	poetry publish

isort:
	poetry run isort .
	poetry run ruff check --select I $(package) tests --fix

isort-check:
	poetry run ruff check --select I $(package) tests
	poetry run isort --diff --check .

ruff:
	poetry run ruff check

fix: format isort
	poetry run ruff check --fix

.ONESHELL:
pyrightconfig:
	jq \
      --null-input \
      --arg venv "$$(basename $$(poetry env info -p))" \
      --arg venvPath "$$(dirname $$(poetry env info -p))" \
      '{ "venv": $$venv, "venvPath": $$venvPath }' \
      > pyrightconfig.json

rename:
	ack antgent -l | xargs -i{} sed -r -i "s/antgent/antgent/g" {}
	ack Antgent -i -l | xargs -i{} sed -r -i "s/Antgent/Antgent/g" {}
	ack ANTGENT -i -l | xargs -i{} sed -r -i "s/ANTGENT/ANTGENT/g" {}

run-worker:
	poetry run bin/antgent  looper --namespace default  --host 127.0.0.1:7233 --config=localconfig.yaml

run-server:
	./bin/antgent server --config localconfig.yaml

temporal-init-namespace:
	temporal operator namespace  create -n antgent-dev-al --retention 72h0m0s --description "antgent stg namespace"

ipython:
	poetry run ipython

temporal-schedule:
	poetry run bin/antgent scheduler --namespace default  --host 127.0.0.1:7233  --config=localconfig.yaml -s scheduly.yaml

docker-push: docker-build
	docker push  ghcr.io/ant31/antgent:latest

docker-build:
	docker build --network=host -t ghcr.io/ant31/antgent:latest .
