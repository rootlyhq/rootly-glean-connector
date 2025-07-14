# Rootly Glean Connector

A Python integration that syncs Rootly incident management data with Glean for unified search and discovery.

## Overview

This project creates a seamless connection between Rootly and Glean, enabling users to search for:

- **Incidents** - Active and resolved incidents with severity, status, and timeline data
- **Alerts** - Alert configurations and monitoring rules
- **Retrospectives** - Post-incident analysis with link to document on Rootly

## Quick Start

## Requirements

- **Python 3.13+** 
  ```bash
  # macOS (using Homebrew)
  brew install python@3.13
  ``` 

1. **Clone and setup environment:**
   ```bash
   git clone https://github.com/rootlyhq/rootly-glean-connector.git
   cd rootly-glean-connector
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get secrets file:**
   Create a `secrets.env` file containing:
   ```
   GLEAN_API_TOKEN=your_glean_api_token_here
   ROOTLY_API_TOKEN=your_rootly_api_token_here
   ```

4. **Run the integration:**
   ```bash
   python app.py
   ```

## Configuration

Edit `config.json` to customize:
- **Glean API host** - Update `glean.api_host` to match your Glean server (default: `support-lab-be.glean.com`)
- Data type settings (enable/disable incidents, alerts, schedules, escalation policies, retrospectives)
- Item limits and pagination per data type
- Enhanced incident features (timeline events, action items)
- Logging levels and sync intervals

Configuration files:
- `config.json` - Contains non-sensitive configuration settings
- `secrets.env` - Contains API tokens

## Architecture

- **data_fetchers/**: API clients for each Rootly data type
- **document_mappers/**: Convert Rootly data to Glean document format
- **processors/**: Sync coordination and orchestration
- **glean_schema/**: Glean document definitions

## Advanced Usage

**Run with date filter:**
```bash
python app.py 2024-01-01T00:00:00Z
```
