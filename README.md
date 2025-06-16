# Rootly to Glean Integration

A Python integration that syncs Rootly incident management data with Glean for unified search and discovery.

## Overview

This project creates a seamless connection between Rootly and Glean, enabling users to search incidents, alerts, schedules, and escalation policies directly within Glean's interface. The integration includes enhanced incident features with timeline events, action items, and detailed severity information.

## Features

- **Multi-Data Type Support**: Incidents, alerts, schedules, and escalation policies
- **Enhanced Incident Data**: Timeline events, action items, and detailed severity information
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
   source venv/bin/activate  # On Windows: venv\Scripts\activate
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
- Data type settings (enable/disable incidents, alerts, etc.)
- Item limits and pagination
- Enhanced incident features
- Logging levels

## Glean Search

Once synced, search for Rootly data in Glean:
- Incident numbers: `INC-123`
- By severity: `severity:high`
- By status: `status:resolved` 
- Timeline events and action items are embedded in incident documents

## Architecture

- **Data Fetchers**: Modular API clients for each Rootly data type
- **Document Mappers**: Convert Rootly data to Glean document format
- **Sync Coordinator**: Orchestrates multi-data-type synchronization
- **Enhanced Features**: Timeline events, action items, and detailed metadata

## Contact

For API tokens and setup assistance, contact **Spencer**.