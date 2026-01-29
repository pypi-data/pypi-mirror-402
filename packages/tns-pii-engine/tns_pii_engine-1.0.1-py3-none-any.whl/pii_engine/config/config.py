#!/usr/bin/env python3
"""
Simple Config Loader for PII Engine
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Simple configuration loader for fabricator.json"""
    
    @staticmethod
    def load_fabricator():
        """Load fabricator configuration from config folder"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'fabricator.json')
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load fabricator.json: {e}")
            raise
    
    @staticmethod
    def extract_product_config(fabricator_config):
        """Extract product-specific configuration"""
        try:
            # Get the first product config (employment_exchange)
            product_configs = fabricator_config.get('product_specific_config', {})
            if not product_configs:
                raise ValueError("No product configurations found")
            
            # Get first product config
            product_name = list(product_configs.keys())[0]
            config = product_configs[product_name]
            
            return config
            
        except Exception as e:
            #print(f"ERROR: Failed to extract product config: {e}")
            raise