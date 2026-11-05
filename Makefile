.PHONY: lint fmt test check

lint: ## Run ruff linter
	python3 -m ruff check .

fmt: ## Format code with ruff
	python3 -m ruff format .

test: ## Run offline startup and SDK regression tests
	python3 -m unittest discover -s tests -v

check: lint test ## Run all checks (lint, tests, and format check)
	python3 -m ruff format --check .
