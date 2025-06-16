"""
Alert data fetcher for Rootly API
"""

import logging
from typing import List, Dict, Optional
from .base import RootlyDataFetcher

logger = logging.getLogger(__name__)


def fetch_alerts(
    updated_after: Optional[str] = None,
    max_items: Optional[int] = None,
    items_per_page: int = 10
) -> List[Dict]:
    """
    Fetch alerts from Rootly API
    
    Args:
        updated_after: ISO 8601 timestamp to filter alerts
        max_items: Maximum number of alerts to fetch
        items_per_page: Number of items per page
        
    Returns:
        List of alert dictionaries
    """
    fetcher = RootlyDataFetcher()
    
    logger.info(f"Fetching alerts, max_items: {max_items}")
    return fetcher.fetch_paginated_data(
        endpoint="alerts",
        updated_after=updated_after,
        max_items=max_items,
        items_per_page=items_per_page
    )