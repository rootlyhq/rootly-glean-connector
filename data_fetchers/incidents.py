"""
Incident data fetcher for Rootly API with enhanced data (timelines, RCAs, etc.)
"""

import logging
from typing import List, Dict, Optional, Any
from .base import RootlyDataFetcher

logger = logging.getLogger(__name__)


def fetch_incidents(
    updated_after: Optional[str] = None, 
    target_page: Optional[int] = None, 
    items_per_page: int = 10,
    max_items: Optional[int] = None
) -> List[Dict]:
    """
    Fetch incidents from Rootly API
    
    Args:
        updated_after: ISO 8601 timestamp to filter incidents
        target_page: Specific page to fetch (for backwards compatibility)
        items_per_page: Number of items per page
        max_items: Maximum number of items to fetch
        
    Returns:
        List of incident dictionaries
    """
    fetcher = RootlyDataFetcher()
    
    # Handle backwards compatibility with target_page parameter
    if target_page:
        logger.info(f"Fetching specific page {target_page} of incidents")
        params = {
            "page[size]": items_per_page,
            "page[number]": target_page
        }
        if updated_after:
            params["updated_after"] = updated_after
        
        try:
            payload = fetcher._make_request("incidents", params)
            items = payload.get("data", [])
            logger.info(f"Fetched {len(items)} incidents from page {target_page}")
            return items
        except Exception as e:
            logger.error(f"Error fetching incidents page {target_page}: {e}")
            return []
    
    # Use paginated fetching for new approach
    logger.info(f"Fetching incidents with pagination, max_items: {max_items}")
    return fetcher.fetch_paginated_data(
        endpoint="incidents",
        updated_after=updated_after,
        max_items=max_items,
        items_per_page=items_per_page
    )