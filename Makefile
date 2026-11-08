ROOT_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
ENV_FILE := $(or $(HM_ANALYTICS_DIR),$(CURDIR))/.env

# Initialisation recipes
.PHONY: setup
setup: ## Install uv and pre-commit
	@if ! command -v uv; then \
		echo "Installing uv package manager..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	else \
		echo "uv is already installed. Checking for updates..."; \
		uv self update; \
	fi
	uv sync
	uv run pre-commit install --install-hooks

.PHONY: lock
lock: setup ## Generate uv.lock
	uv lock

.PHONY: lint
lint:  ## Run linters
	@echo "\\033[0;34mDagster checks\\033[0m"
	#DAGSTER_POSTGRESQL_HOST="localhost" uv run dg check defs
	uv run dg check toml
	uv run dg check yaml
	@echo "\\033[0;34mpre-commit checks\\033[0m"
	uv run pre-commit run --all-files --hook-stage pre-commit
	@echo "\\033[0;34mpre-push checks\\033[0m"
	uv run pre-commit run --all-files --hook-stage pre-push

.PHONY: dev
dev:  ## Run Dagster locally (without Docker)
	uv run --env-file .env dg dev

.PHONY: serve
serve:  ## Serve the Dagster web server locally (via Docker)
	docker compose \
		--env-file $(ENV_FILE) \
		--project-name hm_analytics \
		--file docker-compose.yaml \
		up --detach --build
	@echo "Dagster GUI running on http://localhost:3000"

.PHONY: teardown
teardown:  ## Tear down the local Dagster web server
	docker compose \
		--file docker-compose.yaml \
		down --remove-orphans


.PHONY: clean
clean: ## Uninstall pre-commit and the virtual environment
	@echo Uninstalling pre-commit and the virtual environment.
	uv run pre-commit uninstall
	rm -rf $(ROOT_DIR).venv

.PHONY: help
help:	## Show targets and comments (must have ##)
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' -e 's/##//'
