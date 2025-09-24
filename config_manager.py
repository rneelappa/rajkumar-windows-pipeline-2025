#!/usr/bin/env python3
"""
Configuration Manager
=====================

Handles loading and managing configuration from YAML file.
"""

import yaml
import os
from typing import Dict, Any, Optional
import logging

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(f"Configuration file {self.config_file} not found")
            
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            
            logging.info(f"Configuration loaded from {self.config_file}")
            
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_company_id(self) -> str:
        """Get company ID"""
        return self.get('company.id')
    
    def get_division_id(self) -> str:
        """Get division ID"""
        return self.get('company.division_id')
    
    def get_tally_company_name(self) -> str:
        """Get Tally company name"""
        return self.get('company.tally_name')
    
    def get_tally_url(self) -> str:
        """Get Tally server URL"""
        return self.get('tally.url')
    
    def get_tally_timeout(self) -> int:
        """Get Tally request timeout"""
        return self.get('tally.timeout', 120)
    
    def get_supabase_schema(self) -> str:
        """Get Supabase schema name"""
        return self.get('supabase.schema')
    
    def get_supabase_url(self) -> str:
        """Get Supabase connection URL"""
        return self.get('supabase.url')
    
    def get_supabase_config(self) -> Dict[str, Any]:
        """Get Supabase connection configuration"""
        return self.get('supabase.connection', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.get('database', {})
    
    def get_migration_config(self) -> Dict[str, Any]:
        """Get migration configuration"""
        return self.get('migration', {})
    
    def validate_config(self) -> bool:
        """Validate required configuration values"""
        required_keys = [
            'company.id',
            'company.division_id', 
            'company.tally_name',
            'tally.url',
            'supabase.schema',
            'supabase.url'
        ]
        
        missing_keys = []
        for key in required_keys:
            if self.get(key) is None:
                missing_keys.append(key)
        
        if missing_keys:
            logging.error(f"Missing required configuration keys: {missing_keys}")
            return False
        
        return True

# Global config instance
config = ConfigManager()
