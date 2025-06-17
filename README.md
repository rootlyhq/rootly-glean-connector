# Rootly to Glean Integration

A Python integration that syncs Rootly incident management data with Glean for unified search and discovery.

## Overview

This project creates a seamless connection between Rootly and Glean, enabling users to search incidents, alerts, schedules, escalation policies, and retrospectives directly within Glean's interface. The integration includes enhanced incident features with timeline events, action items, detailed severity information, and comprehensive postmortem analysis.

## Architecture

- **data_fetchers/**: API clients for each Rootly data type
- **document_mappers/**: Convert Rootly data to Glean document format
- **processors/**: Sync coordination and orchestration
- **glean_schema/**: Glean document definitions

## Features

- **Multi-Data Type Support**: Incidents, alerts, schedules, escalation policies, and retrospectives
- **Enhanced Incident Data**: Timeline events, action items, and detailed severity information
- **Comprehensive Retrospectives**: What went well, improvements, lessons learned, and action items
- **Modular Architecture**: Separate data fetchers and document mappers for each data type
- **Configuration Management**: Structured config with separated secrets management
- **Real-time Sync**: Configurable sync intervals and filtering options

## Requirements

- **Python 3.13+** (uses modern union syntax and latest features)
- Virtual environment recommended

## Setup

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd rootly_glean_integration
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get secrets file:**
   Contact **Spencer** for the `secrets.env` file containing API tokens.

4. **Configuration:**
   - `config.json` - Contains non-sensitive configuration settings
   - `secrets.env` - Contains API tokens (obtained from Spencer)

## Usage

**Run the integration:**
```bash
python app.py
```

**Run with date filter:**
```bash
python app.py 2024-01-01T00:00:00Z
```

## Configuration

Edit `config.json` to customize:
- Data type settings (enable/disable incidents, alerts, schedules, escalation policies, retrospectives)
- Item limits and pagination per data type
- Enhanced incident features (timeline events, action items)
- Logging levels and sync intervals

## Glean Search

Once synced, search for Rootly data in Glean:
- **Incidents**: `INC-123`, `severity:high`, `status:resolved`
- **Retrospectives**: `objectType:Retrospective`, `type:retrospective`
- **Linked Content**: `incident:123` (find retrospectives for specific incidents)
- **Timeline Events**: Embedded in incident documents with timestamps
- **Action Items**: From both incidents and retrospectives
- **Postmortem Analysis**: "what went well", "lessons learned", improvement suggestions


