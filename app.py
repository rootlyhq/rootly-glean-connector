#!/usr/bin/env python3
"""
One‑file Rootly → Glean sync with inline settings.
"""

import os
import logging
import time

# Import configuration management
from config import get_config, config_manager

# Load configuration
config = get_config()

# Setup logging based on configuration
logging.basicConfig(
    level=getattr(logging, config.logging.level),
    format=config.logging.format
)
logging.getLogger("httpx").setLevel(logging.DEBUG)

logging.info("Configuration loaded successfully")
logging.info(f"Using Glean datasource: {config.glean.datasource_name}")
logging.info(f"Using Glean host: {config.glean.api_host}")
logging.info(f"Processing up to {config.processing.max_incidents} incidents")

# ----------------- 2. Libraries -----------------------

import requests, sys, json, uuid
from typing import List, Optional, Union
from dateutil import parser as dtparse
import httpx # Import httpx for type hinting for the hook

from glean.api_client import Glean, models, errors as glean_errors

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
    
    # Create the datasource configuration
    config_payload = models.CustomDatasourceConfig(
        name=config.glean.datasource_name,
        display_name=config.glean.display_name,
        datasource_category="TICKETS",
        url_regex="https://rootly.com/account/incidents/.*",
        object_definitions=[models.ObjectDefinition(name="Incident", doc_category="TICKETS")]
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

def bulk_index(client: Glean, docs: List[dict]) -> None:
    logging.info(f"Attempting to index {len(docs)} documents (Refactoring needed)...")
    # TODO: Refactor this function using the new 'client' (glean.Glean)
    # Example: client.indexing.documents.index(documents=docs, datasource=DATASOURCE_NAME)
    pass

# ----------------- 4. Rootly helpers ------------------

def fetch_incidents(updated_after: Optional[str] = None, target_page: Optional[int] = None, items_per_page: int = 10) -> List[dict]:
    logging.info(f"Fetching incidents from Rootly, updated after: {updated_after if updated_after else 'N/A'}, target page: {target_page}")
    
    hdrs = {
        "Authorization": f"Bearer {config.rootly.api_token}",
        "Content-Type" : "application/vnd.api+json",
    }
    params = {
        "updated_after": updated_after if updated_after else None,
        "page[size]": items_per_page,  # Set page size
        "page[number]": target_page if target_page else 1  # Directly set page number
    }
    params = {k: v for k, v in params.items() if v is not None}  # Remove None values
    url = f"{config.rootly.api_base}/incidents"
    
    try:
        logging.info(f"Fetching page {target_page} directly from {url} with params: {params}")
        r = requests.get(url, headers=hdrs, params=params, timeout=30)
        r.raise_for_status()
        payload = r.json()
        items = payload["data"]
        logging.info(f"Successfully fetched {len(items)} items from page {target_page}")
        return items
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching incidents from Rootly (page {target_page}, URL: {url}): {e}")
        return []

    return items

def to_doc(i: dict) -> models.DocumentDefinition | None:
    try:
        # Safely access attributes
        a = i.get("attributes")
        if not a:
            logging.error(f"Incident ID {i.get('id', 'Unknown ID')} is missing 'attributes' or 'attributes' is None. Skipping.")
            return None

        # Build document fields, only including non-null values, using snake_case for model fields
        doc_fields = {
            "id": i["id"],
            "datasource": config.glean.datasource_name,
            "title": f"[INC-{a.get('sequential_id', 'N/A')}] {a.get('title', 'No Title')}",
            "object_type": "Incident",  # Changed to snake_case
            "view_url": a.get("url"),     # Changed to snake_case
            "permissions": {
                "allow_anonymous_access": True  # Changed to snake_case
            }
        }

        # Add status if exists
        if status := a.get('status'):
            doc_fields["status"] = status
            if "tags" not in doc_fields:
                doc_fields["tags"] = []
            doc_fields["tags"].append(f"status:{status}")

        # Handle severity data safely
        if severity := a.get('severity'):
            if isinstance(severity, dict) and (severity_data := severity.get('data', {}).get('attributes', {})):
                severity_name = severity_data.get('name')
                # severity_desc = severity_data.get('description', '') # Not directly used in doc_fields
                if severity_name and severity_name != "Unknown":
                    if "tags" not in doc_fields:
                        doc_fields["tags"] = []
                    doc_fields["tags"].append(f"severity:{severity_name}")

        # Add kind tag if exists
        if kind := a.get('kind'):
            if "tags" not in doc_fields:
                doc_fields["tags"] = []
            doc_fields["tags"].append(f"kind:{kind}")

        # Build content string
        content_parts = []
        content_parts.append(f"Title: {a.get('title', 'No Title')}")
        if status: # status already checked and added to doc_fields
            content_parts.append(f"Status: {status}")

        # Add summary if exists
        if summary_text := a.get("summary"):
            content_parts.append(f"\nSummary:\n{summary_text}")
            doc_fields["summary"] = { # 'summary' is the field name for the Content model
                "mime_type": "text/plain",    # Changed to snake_case
                "text_content": summary_text  # Changed to snake_case
            }

        # Add action items if they exist
        if action_items := i.get('relationships', {}).get('action_items', {}).get('data', []):
            content_parts.append("\nAction Items:")
            for item in action_items:
                content_parts.append(f"- {item.get('id', 'Unknown Action Item')}")

        # Add body content
        doc_fields["body"] = { # 'body' is the field name for the Content model
            "mime_type": "text/plain",        # Changed to snake_case
            "text_content": "\n".join(content_parts)  # Changed to snake_case
        }

        # Add author if available
        if user_data := a.get('user', {}).get('data', {}).get('attributes', {}):
            author_details = {}
            if full_name := user_data.get('full_name'):
                author_details["name"] = full_name
            if email := user_data.get('email'):
                author_details["email"] = email
            if author_details: # If any author details were found
                doc_fields["author"] = author_details # 'author' is the field name for Author model

        # Add timestamps if available, using snake_case for model fields
        for ts_model_field, src_api_field in [("created_at", "created_at"), ("updated_at", "updated_at")]:
            if ts_api_value := a.get(src_api_field):
                try:
                    doc_fields[ts_model_field] = int(dtparse.isoparse(ts_api_value).timestamp())
                except (ValueError, TypeError):
                    logging.warning(f"Could not parse {src_api_field}: {ts_api_value}")

        logging.info(f"Document fields for Pydantic model: {json.dumps(doc_fields, indent=2)}")
        return models.DocumentDefinition(**doc_fields)

    except Exception as e:
        logging.error(f"Error creating document for incident {i.get('id', 'Unknown ID')}: {e}", exc_info=True)
        return None

# ----------------- 5. Main flow -----------------------

if __name__ == "__main__":
    logging.info("Script starting for bulk incident processing...")
    
    # Configuration is already loaded and validated at module level

    since = sys.argv[1] if len(sys.argv) > 1 else None
    if since:
        try:
            dtparse.isoparse(since)              # validate ISO‑8601
            logging.info(f"Processing incidents since: {since}")
        except ValueError as e:
            logging.error(f"Invalid 'since' date format: {since}. Error: {e}. Please use ISO-8601 format (e.g., YYYY-MM-DDTHH:MM:SSZ).")
            sys.exit(1)
    else:
        logging.info(f"No 'since' date provided; fetching incidents up to {config.processing.max_incidents} from the first {config.processing.max_pages} pages.")

    try:
        with glean_client() as c:
            ensure_datasource(c)  # Create/update the datasource first
            
            all_incidents_data = []

            logging.info(f"Starting to fetch incidents from Rootly, up to {config.processing.max_pages} pages or {config.processing.max_incidents} incidents...")
            for page_num in range(1, config.processing.max_pages + 1):
                if len(all_incidents_data) >= config.processing.max_incidents:
                    logging.info(f"Reached max incidents ({config.processing.max_incidents}). Stopping fetch.")
                    break
                logging.info(f"Fetching page {page_num} from Rootly...")
                # Calculate remaining items to fetch to not exceed max_incidents
                remaining_slots = config.processing.max_incidents - len(all_incidents_data)
                current_items_per_page = min(config.processing.items_per_page, remaining_slots) if remaining_slots > 0 else config.processing.items_per_page
                
                if current_items_per_page <= 0 and len(all_incidents_data) >= config.processing.max_incidents:
                    break
                    
                page_incidents = fetch_incidents(updated_after=since, target_page=page_num, items_per_page=current_items_per_page)
                if not page_incidents:
                    logging.info(f"No incidents found on page {page_num}. Assuming no more incidents.")
                    break # Stop if a page returns no incidents
                all_incidents_data.extend(page_incidents)
                logging.info(f"Fetched {len(page_incidents)} incidents from page {page_num}. Total fetched: {len(all_incidents_data)}.")
            
            # Ensure we don't process more than max_incidents
            incidents_to_process = all_incidents_data[:config.processing.max_incidents]
            logging.info(f"Total incidents to process after fetching: {len(incidents_to_process)}")

            if not incidents_to_process:
                logging.info("No incidents fetched or to process. Exiting.")
                sys.exit(0)

            docs_to_index = []
            logging.info(f"\n--- Converting {len(incidents_to_process)} incidents to Glean documents ---")
            for count, incident_data in enumerate(incidents_to_process):
                logging.debug(f"Processing incident {count+1}/{len(incidents_to_process)}, ID: {incident_data.get('id')}")
                doc = to_doc(incident_data)
                if doc:
                    docs_to_index.append(doc)
                else:
                    logging.warning(f"Failed to convert incident ID {incident_data.get('id')} to document. Skipping.")
            
            if not docs_to_index:
                logging.info("No documents were successfully converted for indexing. Exiting.")
                sys.exit(0)

            logging.info(f"\n--- Attempting to bulk index {len(docs_to_index)} documents ---")
            try:
                index_api_response = c.indexing.documents.index(
                    datasource=config.glean.datasource_name,
                    documents=docs_to_index # Pass the list of DocumentDefinition objects
                )
                logging.info(f"✔ Successfully initiated bulk indexing for {len(docs_to_index)} documents. Response: {index_api_response}")

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

            logging.info("\n--- Bulk processing finished ---")

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
