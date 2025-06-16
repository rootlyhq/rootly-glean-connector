"""
Glean object definitions for different Rootly data types
"""

from glean.api_client import models
from typing import List


def get_object_definitions() -> List[models.ObjectDefinition]:
    """
    Get all object definitions for Rootly datasource
    
    Returns:
        List of ObjectDefinition objects for all supported data types
    """
    return [
        # Incident object definition
        models.ObjectDefinition(
            name="Incident",
            display_label="Incident",
            doc_category="TICKETS",
            summarizable=True
        ),
        
        # Alert object definition
        models.ObjectDefinition(
            name="Alert",
            display_label="Alert",
            doc_category="TICKETS",
            summarizable=True
        ),
        
        # Schedule object definition
        models.ObjectDefinition(
            name="Schedule",
            display_label="Schedule",
            doc_category="UNCATEGORIZED",
            summarizable=True
        ),
        
        # Escalation Policy object definition
        models.ObjectDefinition(
            name="EscalationPolicy",
            display_label="Escalation Policy",
            doc_category="UNCATEGORIZED",
            summarizable=True
        )
    ]


def get_incident_object_definition() -> models.ObjectDefinition:
    """Get specific object definition for incidents"""
    return models.ObjectDefinition(
        name="Incident",
        display_label="Incident",
        doc_category="TICKETS",
        summarizable=True
    )


def get_alert_object_definition() -> models.ObjectDefinition:
    """Get specific object definition for alerts"""
    return models.ObjectDefinition(
        name="Alert",
        display_label="Alert", 
        doc_category="TICKETS",
        summarizable=True
    )


def get_schedule_object_definition() -> models.ObjectDefinition:
    """Get specific object definition for schedules"""
    return models.ObjectDefinition(
        name="Schedule",
        display_label="Schedule",
        doc_category="UNCATEGORIZED",
        summarizable=True
    )


def get_escalation_policy_object_definition() -> models.ObjectDefinition:
    """Get specific object definition for escalation policies"""
    return models.ObjectDefinition(
        name="EscalationPolicy",
        display_label="Escalation Policy",
        doc_category="UNCATEGORIZED",
        summarizable=True
    )