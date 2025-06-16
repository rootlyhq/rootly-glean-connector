"""
Retrospectives data fetcher for Rootly API
"""

import logging
from typing import List, Dict, Optional
from .base import RootlyDataFetcher

logger = logging.getLogger(__name__)


def fetch_retrospectives(
    updated_after: Optional[str] = None,
    max_items: Optional[int] = None,
    items_per_page: int = 10
) -> List[Dict]:
    """
    Fetch retrospectives from Rootly API
    
    Args:
        updated_after: ISO 8601 timestamp to filter retrospectives
        max_items: Maximum number of retrospectives to fetch
        items_per_page: Number of items per page
        
    Returns:
        List of retrospective dictionaries
    """
    fetcher = RootlyDataFetcher()
    
    logger.info(f"Fetching retrospectives, max_items: {max_items}")
    retrospectives = fetcher.fetch_paginated_data(
        endpoint="post_mortems",
        updated_after=updated_after,
        max_items=max_items,
        items_per_page=items_per_page
    )
    
    logger.info(f"Successfully fetched {len(retrospectives)} retrospectives")
    return retrospectives