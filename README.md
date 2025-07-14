# Rootly Glean Connector

A Python integration that syncs Rootly incident management data with Glean for unified search and discovery.

## Overview

This project creates a seamless connection between Rootly and Glean, enabling users to search for:

- **Incidents** - Active and resolved incidents with severity, status, and timeline data
- **Alerts** - Alert configurations and monitoring rules
- **Schedules** - On-call schedules with rotations, shifts, and user assignments
- **Escalation Policies** - Links to escalation rules and notification chains
- **Retrospectives** - Links to post-incident analysis

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

## Glean Search Examples

Once synced, search for Rootly data in Glean:

### Incidents
- `INC-123` - Find specific incidents
- `severity:high` - Filter by severity level
- `status:resolved` - Find resolved incidents
- `"Find me incidents with timeline events"` - Incidents with detailed timeline data
- `"Show me incidents with high severity that are resolved"` - High severity resolved incidents

### Schedules & On-Call
- `"Jerry's schedule"` - Find schedules by user name
- `"on call today"` - Current on-call assignments
- `"schedule overrides"` - Override shifts and coverage
- `"Adam Frank"` - Find schedules for specific users
- `"Show me schedule rotations in rootly"` - Schedule rotation patterns and timing
- `"Show me latest on-call schedule in rootly"` - Current and upcoming on-call assignments

### Alerts & Monitoring
- `alert` - All alert configurations
- `monitoring rules` - Alert routing and urgency settings

### Escalation & Policies
- `escalation policy` - Notification chains and rules
- `"The Razors Team"` - Team-specific policies

### Retrospectives
- `retrospective` - Post-incident analysis
- `lessons learned` - Retrospective insights

## Advanced Usage

**Run with date filter:**
```bash
python app.py 2024-01-01T00:00:00Z
```
