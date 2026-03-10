.PHONY: lint fmt check

lint: ## Run ruff linter
	python3 -m ruff check .

fmt: ## Format code with ruff
	python3 -m ruff format .

check: lint ## Run all checks (lint + format check)
	python3 -m ruff format --check .
