"""
Escalation policy data fetcher for Rootly API
"""

import logging
from typing import List, Dict, Optional
from .base import RootlyDataFetcher

logger = logging.getLogger(__name__)


def fetch_escalation_policies(
    updated_after: Optional[str] = None,
    max_items: Optional[int] = None,
    items_per_page: int = 10
) -> List[Dict]:
    """
    Fetch escalation policies from Rootly API
    
    Args:
        updated_after: ISO 8601 timestamp to filter policies
        max_items: Maximum number of policies to fetch
        items_per_page: Number of items per page
        
    Returns:
        List of escalation policy dictionaries
    """
    fetcher = RootlyDataFetcher()
    
    logger.info(f"Fetching escalation policies, max_items: {max_items}")
    return fetcher.fetch_paginated_data(
        endpoint="escalation_policies",
        updated_after=updated_after,
        max_items=max_items,
        items_per_page=items_per_page
    )