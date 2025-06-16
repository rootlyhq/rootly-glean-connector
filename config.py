#!/usr/bin/env python3
"""
Configuration management for Rootly → Glean integration
Follows security best practices by separating config from secrets
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class GleanConfig:
    api_host: str
    api_token: str
    datasource_name: str
    display_name: str


@dataclass
class RootlyConfig:
    api_base: str
    api_token: str


@dataclass
class EnhancedDataConfig:
    include_events: bool
    include_action_items: bool


@dataclass
class DataTypeConfig:
    enabled: bool
    max_items: int
    items_per_page: int


@dataclass
class IncidentDataTypeConfig(DataTypeConfig):
    enhanced_data: EnhancedDataConfig


@dataclass
class DataTypesConfig:
    incidents: IncidentDataTypeConfig
    alerts: DataTypeConfig
    schedules: DataTypeConfig
    escalation_policies: DataTypeConfig


@dataclass
class ProcessingConfig:
    max_pages: int
    sync_interval_minutes: int


@dataclass
class LoggingConfig:
    level: str
    format: str


@dataclass
class AppConfig:
    glean: GleanConfig
    rootly: RootlyConfig
    data_types: DataTypesConfig
    processing: ProcessingConfig
    logging: LoggingConfig


class ConfigManager:
    """Manages application configuration with security best practices"""
    
    def __init__(self, config_file: str = "config.json", secrets_file: str = "secrets.env"):
        self.config_file = Path(config_file)
        self.secrets_file = Path(secrets_file)
        self._config: Optional[AppConfig] = None
    
    def load_config(self) -> AppConfig:
        """Load configuration from files with validation"""
        if self._config is not None:
            return self._config
        
        # Load secrets first
        secrets = self._load_secrets()
        
        # Load configuration
        config_data = self._load_config_file()
        
        # Validate required secrets
        required_secrets = ["GLEAN_API_TOKEN", "ROOTLY_API_TOKEN"]
        missing_secrets = [key for key in required_secrets if not secrets.get(key)]
        if missing_secrets:
            raise ValueError(f"Missing required secrets: {', '.join(missing_secrets)}")
        
        # Build configuration objects
        try:
            self._config = AppConfig(
                glean=GleanConfig(
                    api_host=config_data["glean"]["api_host"],
                    api_token=secrets["GLEAN_API_TOKEN"],
                    datasource_name=config_data["glean"]["datasource_name"],
                    display_name=config_data["glean"]["display_name"]
                ),
                rootly=RootlyConfig(
                    api_base=config_data["rootly"]["api_base"],
                    api_token=secrets["ROOTLY_API_TOKEN"]
                ),
                data_types=DataTypesConfig(
                    incidents=IncidentDataTypeConfig(
                        enabled=config_data["data_types"]["incidents"]["enabled"],
                        max_items=config_data["data_types"]["incidents"]["max_items"],
                        items_per_page=config_data["data_types"]["incidents"]["items_per_page"],
                        enhanced_data=EnhancedDataConfig(
                            include_events=config_data["data_types"]["incidents"]["enhanced_data"]["include_events"],
                            include_action_items=config_data["data_types"]["incidents"]["enhanced_data"]["include_action_items"]
                        )
                    ),
                    alerts=DataTypeConfig(
                        enabled=config_data["data_types"]["alerts"]["enabled"],
                        max_items=config_data["data_types"]["alerts"]["max_items"],
                        items_per_page=config_data["data_types"]["alerts"]["items_per_page"]
                    ),
                    schedules=DataTypeConfig(
                        enabled=config_data["data_types"]["schedules"]["enabled"],
                        max_items=config_data["data_types"]["schedules"]["max_items"],
                        items_per_page=config_data["data_types"]["schedules"]["items_per_page"]
                    ),
                    escalation_policies=DataTypeConfig(
                        enabled=config_data["data_types"]["escalation_policies"]["enabled"],
                        max_items=config_data["data_types"]["escalation_policies"]["max_items"],
                        items_per_page=config_data["data_types"]["escalation_policies"]["items_per_page"]
                    )
                ),
                processing=ProcessingConfig(
                    max_pages=config_data["processing"]["max_pages"],
                    sync_interval_minutes=config_data["processing"]["sync_interval_minutes"]
                ),
                logging=LoggingConfig(
                    level=config_data["logging"]["level"],
                    format=config_data["logging"]["format"]
                )
            )
            
            logging.info("Configuration loaded successfully")
            logging.info(f"Using Glean datasource: {self._config.glean.datasource_name}")
            logging.info(f"Using Glean host: {self._config.glean.api_host}")
            
            return self._config
            
        except KeyError as e:
            raise ValueError(f"Missing required configuration key: {e}")
    
    def _load_secrets(self) -> Dict[str, str]:
        """Load secrets from environment file"""
        if not self.secrets_file.exists():
            raise FileNotFoundError(f"Secrets file not found: {self.secrets_file}")
        
        # Load environment variables from secrets file
        load_dotenv(self.secrets_file, verbose=True, override=True)
        
        return {
            "GLEAN_API_TOKEN": os.getenv("GLEAN_API_TOKEN", ""),
            "ROOTLY_API_TOKEN": os.getenv("ROOTLY_API_TOKEN", "")
        }
    
    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def get_instance_name(self) -> str:
        """Extract Glean instance name from API host"""
        config = self.load_config()
        hostname = config.glean.api_host
        
        # Extract instance name from hostname
        instance_name = hostname.split('.')[0]
        if '-be' in instance_name:
            instance_name = instance_name.split('-be')[0]
        
        if not instance_name:
            raise ValueError(f"Could not derive instance name from host: {hostname}")
        
        return instance_name


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """Get the application configuration"""
    return config_manager.load_config()