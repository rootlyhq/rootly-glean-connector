#!/usr/bin/env python3
"""
One‑file Rootly → Glean sync with inline settings.
"""

import os
import logging
import time

import coloredlogs

# Import configuration management
from config import get_config, config_manager

# Load configuration
config = get_config()
coloredlogs.install(
    level=config.logging.level,
    fmt=config.logging.format,
)
logging.getLogger("httpx").setLevel(logging.INFO)

logging.info("Configuration loaded successfully")
logging.info(f"Using Glean datasource: {config.glean.datasource_name}")
logging.info(f"Using Glean host: {config.glean.api_host}")
logging.info(f"Enabled data types: incidents({config.data_types.incidents.enabled}), alerts({config.data_types.alerts.enabled}), schedules({config.data_types.schedules.enabled}), escalation_policies({config.data_types.escalation_policies.enabled})")

# ----------------- 2. Libraries -----------------------

import requests, sys, json, uuid
from typing import List, Optional, Union
from dateutil import parser as dtparse
import httpx # Import httpx for type hinting for the hook

from glean.api_client import Glean, models, errors as glean_errors
from glean_schema import get_object_definitions
from processors import SyncCoordinator

# ----------------- 3. Glean helpers -------------------

def glean_client() -> Glean:
    logging.info("Initializing Glean API client...")
    
    try:
        instance_name = config_manager.get_instance_name()
        logging.info(f"Using instance name: {instance_name}")
        
        # Standard Glean client initialization
        client = Glean(api_token=config.glean.api_token, instance=instance_name)
        logging.info("Glean API client initialized.")
        return client
        
    except Exception as e:
        logging.error(f"Failed to initialize Glean client: {e}")
        raise

# Function to log request details via httpx event hook
def log_request_details(request: httpx.Request):
    request.read() 
    logging.debug(f"--- HTTPX Request Details (Event Hook) ---")
    logging.debug(f"Method: {request.method}, URL: {request.url}")
    logging.debug(f"Headers: {request.headers}")
    logging.debug(f"Raw Request Content Bytes: {request.content!r}")
    if request.content:
        try:
            body_str = request.content.decode('utf-8')
            logging.debug(f"Decoded Request Body (UTF-8):\\n{body_str}")
        except UnicodeDecodeError:
            logging.debug(f"Request Body (bytes, could not decode as UTF-8): {request.content!r}")
    else:
        logging.debug("Request Body: (empty)")
    logging.debug(f"--- End HTTPX Request Details (Event Hook) ---")

def ensure_datasource(client: Glean) -> None:
    logging.info(f"Creating/updating datasource '{config.glean.datasource_name}'...")
    
    # Create the datasource configuration with all object definitions
    config_payload = models.CustomDatasourceConfig(
        name=config.glean.datasource_name,
        display_name=config.glean.display_name,
        datasource_category="TICKETS",
        url_regex="https://rootly.com/account/(incidents|alerts|schedules|escalation_policies)/.*",
        object_definitions=get_object_definitions(),
        aliases=["rootly"],
    )
    
    try:
        logging.info(f"Calling client.indexing.datasources.add with payload: {config_payload}")
        add_response = client.indexing.datasources.add(**config_payload.model_dump())
        logging.info(f"Datasource add/update response: {add_response}")
        logging.info(f"✔ Created/Updated datasource '{config.glean.datasource_name}'")
    except glean_errors.GleanError as e:
        logging.error(f"API error when trying to create/update datasource '{config.glean.datasource_name}': {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error when trying to create/update datasource '{config.glean.datasource_name}': {e}")
        raise

# Old functions removed - now using modular data fetchers and document mappers

# ----------------- 5. Main flow -----------------------

if __name__ == "__main__":
    logging.info("Script starting for multi-data-type Rootly processing...")
    
    # Configuration is already loaded and validated at module level
    sync_coordinator = SyncCoordinator()
    enabled_types = sync_coordinator.get_enabled_data_types()
    logging.info(f"Enabled data types: {', '.join(enabled_types)}")

    since = sys.argv[1] if len(sys.argv) > 1 else None
    if since:
        try:
            dtparse.isoparse(since)              # validate ISO‑8601
            logging.info(f"Processing data since: {since}")
        except ValueError as e:
            logging.error(f"Invalid 'since' date format: {since}. Error: {e}. Please use ISO-8601 format (e.g., YYYY-MM-DDTHH:MM:SSZ).")
            sys.exit(1)
    else:
        logging.info(f"No 'since' date provided; fetching all enabled data types with configured limits.")

    try:
        with glean_client() as c:
            ensure_datasource(c)  # Create/update the datasource first
            
            # Sync all enabled data types
            logging.info("Starting sync of all enabled data types...")
            sync_results, all_documents = sync_coordinator.sync_all_data_types(updated_after=since)
            
            # Log sync results
            logging.info("\\n--- Sync Results Summary ---")
            for data_type, result in sync_results.items():
                if data_type == 'summary':
                    continue
                status = result.get('status', 'unknown')
                if status == 'success':
                    doc_count = result.get('documents_created', 0)
                    logging.info(f"{data_type}: ✅ {doc_count} documents")
                elif status == 'skipped':
                    reason = result.get('reason', 'unknown')
                    logging.info(f"{data_type}: ⏭️  skipped ({reason})")
                else:
                    error = result.get('error', 'unknown error')
                    logging.error(f"{data_type}: ❌ failed - {error}")
            
            total_docs = sync_results.get('summary', {}).get('total_documents', 0)
            logging.info(f"Total documents to index: {total_docs}")

            if not all_documents:
                logging.info("No documents were created from any data type. Exiting.")
                sys.exit(0)

            logging.info(f"\\n--- Attempting to bulk index {len(all_documents)} documents ---")
            
            # Debug: Check for duplicate document IDs
            doc_ids = []
            for i, doc in enumerate(all_documents):
                doc_dict = doc.model_dump() if hasattr(doc, 'model_dump') else doc.__dict__
                doc_id = doc_dict.get('id', f'unknown_{i}')
                if doc_id in doc_ids:
                    logging.error(f"DUPLICATE ID FOUND: {doc_id} in document {i} ({doc_dict.get('title', 'No title')})")
                else:
                    doc_ids.append(doc_id)
                logging.debug(f"Document {i}: ID={doc_id}, Title={doc_dict.get('title', 'No title')}")
                
                # Check for documents with empty view URLs
                if 'viewURL' in doc_dict and not doc_dict['viewURL']:
                    logging.warning(f"Document {i} ({doc_dict.get('title', 'No title')}) has empty viewURL")
                elif 'viewURL' not in doc_dict:
                    logging.debug(f"Document {i} ({doc_dict.get('title', 'No title')}) has no viewURL field")
            
            logging.info(f"Total unique document IDs: {len(set(doc_ids))}, Total documents: {len(all_documents)}")
            
            try:
                index_api_response = c.indexing.documents.index(
                    datasource=config.glean.datasource_name,
                    documents=all_documents
                )
                logging.info(f"✅ Successfully indexed {len(all_documents)} documents. Response: {index_api_response}")

            except glean_errors.GleanError as e_index:
                logging.error(f"Glean API error during bulk document indexing: {e_index}", exc_info=True)
                if hasattr(e_index, 'body') and e_index.body:
                    try:
                        error_details = json.loads(e_index.body)
                        logging.error(f"Glean API error details: {json.dumps(error_details, indent=2)}")
                    except json.JSONDecodeError:
                        logging.error(f"Glean API error body (not JSON): {e_index.body}")
                sys.exit(1)
            except Exception as e_index:
                logging.error(f"Unexpected error during bulk document indexing: {e_index}", exc_info=True)
                sys.exit(1)

            logging.info("\\n--- Multi-data-type sync completed successfully ---")

        logging.info("Script finished successfully.")

    except ValueError as ve:
        logging.error(f"Configuration error: {ve}")
        sys.exit(1)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred with Rootly: {http_err} - Response: {http_err.response.text if http_err.response else 'No response body'}")
        sys.exit(1)
    except glean_errors.GleanError as ge: # Catch Glean specific errors from client operations
        logging.error(f"Glean API or SDK error: {ge}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
