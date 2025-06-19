# Rootly Glean Connector

A Python integration that syncs Rootly incident management data with Glean for unified search and discovery.

## Overview

This project creates a seamless connection between Rootly and Glean, enabling users to search for:

- **Incidents** - Active and resolved incidents with severity, status, and timeline data
- **Alerts** - Alert configurations and monitoring rules
- **Schedules** - On-call schedules and team assignments  
- **Escalation Policies** - Escalation rules and notification chains
- **Retrospectives** - Post-incident analysis with lessons learned and action items

The integration includes enhanced incident features with timeline events, action items, detailed severity information, and postmortem analysis.

## Quick Start

## Requirements

- **Python 3.13+** 
  ```bash
  # macOS (using Homebrew)
  brew install python@3.13
  ``` 

1. **Clone and setup environment:**
   ```bash
   git clone git@github.com:rootlyhq/glean-rootly-connector.git
   cd rootly_glean_integration
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

## Glean Search

Once synced, search for Rootly data in Glean:
- **Incidents**: `INC-123`, `severity:high`, `status:resolved`
- **Retrospectives**: `objectType:Retrospective`, `type:retrospective`
- **Linked Content**: `incident:123` (find retrospectives for specific incidents)
- **Timeline Events**: Embedded in incident documents with timestamps
- **Action Items**: From both incidents and retrospectives
- **Postmortem Analysis**: "what went well", "lessons learned", improvement suggestions


