# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Lint
make lint              # or: python3 -m ruff check .

# Format
make fmt               # or: python3 -m ruff format .

# Both lint + format check
make check

# Run
python app.py                      # full sync
python app.py 2024-01-01T00:00:00Z # sync since timestamp (ISO-8601)

# Setup (creates __rootly__ venv, installs deps including Glean SDK)
bash setup.sh
```

No test suite exists yet.

## Architecture

Rootly API data flows through a three-stage pipeline into Glean's indexing API:

1. **Fetch** (`data_fetchers/`) — `RootlyDataFetcher` base class handles auth headers, paginated requests, and rate limiting against Rootly's JSON:API. Each data type (incidents, alerts, schedules, escalation_policies, retrospectives) has a fetcher module with a top-level `fetch_*()` function. Incidents have an enhanced variant that also pulls timeline events and action items.

2. **Map** (`document_mappers/`) — `BaseDocumentMapper` provides timestamp conversion, author extraction, and base document construction. Each mapper module exposes a `*_to_doc()` function that transforms a single Rootly API dict into a `glean.api_client.models.DocumentDefinition`.

3. **Coordinate** (`processors/sync_coordinator.py`) — `SyncCoordinator` wires fetchers to mappers per data type, respects enabled/disabled flags from config, deduplicates documents by ID, and returns the full document list for bulk indexing.

`app.py` is the entry point: initializes Glean client, ensures the datasource schema exists via `ensure_datasource()`, runs `SyncCoordinator.sync_all_data_types()`, then calls `client.indexing.documents.index()` to bulk-push all documents.

## Configuration

- `config.json` — non-sensitive settings (Glean host, datasource name, per-data-type enable/disable and pagination, processing limits, log level)
- `secrets.env` — `GLEAN_API_TOKEN` and `ROOTLY_API_TOKEN` (loaded via python-dotenv)
- `config.py` — `ConfigManager` singleton merges both files into typed `AppConfig` dataclasses

## Glean SDK

The Glean Python SDK (`glean-api-client`) is installed from a zip at `app.glean.com`, not from PyPI. See `setup.sh`. The `glean_schema/object_definitions.py` file defines the custom datasource schema registered with Glean.

## Linting

Ruff >=0.15.5. Key config in `ruff.toml`: target Python 3.11, line-length 120, double quotes, spaces. `app.py` has per-file ignores for RUF002/RUF003 (unicode characters in log output).
