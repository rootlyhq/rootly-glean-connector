"""
Base data fetcher with common functionality for all Rootly API endpoints
"""

import logging
import requests
from typing import List, Dict, Optional, Any
from config import get_config

logger = logging.getLogger(__name__)


class RootlyDataFetcher:
    """Base class for fetching data from Rootly API"""
    
    def __init__(self):
        self.config = get_config()
        self.headers = {
            "Authorization": f"Bearer {self.config.rootly.api_token}",
            "Content-Type": "application/vnd.api+json",
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make authenticated request to Rootly API"""
        url = f"{self.config.rootly.api_base}/{endpoint.lstrip('/')}"
        
        try:
            logger.debug(f"Making request to {url} with params: {params}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from {url}: {e}")
            raise
    
    def fetch_paginated_data(
        self, 
        endpoint: str, 
        updated_after: Optional[str] = None,
        max_items: Optional[int] = None,
        items_per_page: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch paginated data from Rootly API endpoint"""
        all_items = []
        page = 1
        max_pages = 10  # Safety limit
        
        while page <= max_pages:
            if max_items and len(all_items) >= max_items:
                logger.info(f"Reached max items limit ({max_items}). Stopping fetch.")
                break
            
            params = {
                "page[size]": items_per_page,
                "page[number]": page
            }
            
            if updated_after:
                params["updated_after"] = updated_after
            
            # Calculate remaining items to fetch
            if max_items:
                remaining_slots = max_items - len(all_items)
                params["page[size]"] = min(items_per_page, remaining_slots)
            
            logger.info(f"Fetching page {page} from {endpoint}...")
            
            try:
                payload = self._make_request(endpoint, params)
                items = payload.get("data", [])
                
                if not items:
                    logger.info(f"No items found on page {page}. Stopping fetch.")
                    break
                
                all_items.extend(items)
                logger.info(f"Fetched {len(items)} items from page {page}. Total: {len(all_items)}")
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching page {page} from {endpoint}: {e}")
                break
        
        logger.info(f"Total {len(all_items)} items fetched from {endpoint}")
        return all_items[:max_items] if max_items else all_items
    
    def fetch_single_endpoint(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[List[Dict[str, Any]]]:
        """Fetch data from a single endpoint (non-paginated)"""
        try:
            logger.debug(f"Fetching single endpoint: {endpoint} with params: {params}")
            response = self._make_request(endpoint, params)
            data = response.get("data", [])
            logger.debug(f"Fetched {len(data) if data else 0} items from {endpoint}")
            return data
        except Exception as e:
            logger.warning(f"Failed to fetch from {endpoint}: {e}")
            return None