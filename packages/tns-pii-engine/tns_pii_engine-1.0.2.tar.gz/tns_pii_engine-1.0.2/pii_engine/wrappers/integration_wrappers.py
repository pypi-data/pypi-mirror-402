#!/usr/bin/env python3
"""
Production Integration Wrapper Functions
For FastAPI service integration with dynamic fabricator-based processing
"""

from typing import Optional

import logging
from ..config.settings import settings

logger = logging.getLogger(__name__)


def process_pii_fields(table_name: str, process: str, record_id: Optional[int], field_data: dict) -> dict:
    """
    Process multiple fields for insert/update - Compatible with service 2.py format
    
    Args:
        table_name: Database table name ("jobseekers" or "employers")
        process: "pseudo" or "mask" operation type  
        record_id: Record identifier (None during signup - user doesn't exist yet)
        field_data: Input JSON data
        
    Returns:
        Dict with 'fields' and 'tokenSet' keys as expected by service 2.py
    """
    from ..core.clean_processor import PIIProcessor
    
    pii_processor = PIIProcessor()
    processed_data = {}
    token_set = {}

    # Handle None record_id (use a temporary ID)
    if record_id is None:
        record_id = field_data.get('uid', 999999)

    # Get PII fields dynamically from fabricator.json
    cfg_keys = pii_processor.get_pii_fields_for_process(table_name, process)

    # Map config fields -> actual keys present in the payload
    pii_fields = cfg_keys.intersection(field_data.keys())

    for field_name, field_value in field_data.items():
        if field_name in pii_fields and field_value not in (None, "", "***"):
            if process == "pseudo":
                pseudo_value, token = pii_processor.process_field(
                    table_name, field_name, field_value, record_id
                )
                processed_data[field_name] = pseudo_value
                
                # Store token information for tokenSet
                token_set[field_name] = {
                    "original": field_value,
                    "pseudo": pseudo_value, 
                    "token": token
                }
            else:  # process == "mask"
                pseudo_value = pii_processor.process_field(
                    table_name, field_name, field_value, record_id
                )[0]  # Get only pseudo_value, ignore token
                processed_data[field_name] = pseudo_value
        else:
            processed_data[field_name] = field_value

    # Build TokenSet with tokens for PII fields and original values for non-PII fields
    token_set_output = {}
    for field_name, field_value in field_data.items():
        if field_name in token_set:
            # PII field - use token
            token_set_output[field_name] = token_set[field_name]['token']
        else:
            # Non-PII field - use original value
            token_set_output[field_name] = field_value
    
    # Return format expected by service 2.py - EXACT structure match
    return {
        'TokenSet': token_set_output,
        'fields': processed_data
    }

def retrieve_original_data(_table_name: str, _record_id: int, _field_name: str) -> str:
    """DEPRECATED: Database-free engine does not support direct record retrieval from DB."""
    return ""

def _get_token_data(token_set_json, field_name):
    """Helper to parse token data and return the specific field's token."""
    import json
    if not token_set_json:
        return None
    try:
        if isinstance(token_set_json, str):
            if not token_set_json.strip():
                return None
            data = json.loads(token_set_json)
            if isinstance(data, str): # Handle double encoding
                data = json.loads(data)
        else:
            data = token_set_json
            
        if isinstance(data, dict):
            return data.get(field_name)
    except Exception as e:
        logger.error(f"Error parsing TOKEN_SET for {field_name}: {e}")
    return None

def reverse_pii_fields(_table_name: str, field_name: str, current_value: str, token_set_json: str) -> str:
    """Refactored to reduce complexity and use professional logging."""
    import base64
    from cryptography.fernet import Fernet
    
    encrypted_value = _get_token_data(token_set_json, field_name)
    if not encrypted_value or not isinstance(encrypted_value, str):
        return current_value
        
    if encrypted_value.startswith("EE_"):
        try:
            base64_data = encrypted_value[3:]
            key = settings.PII_ENC_KEY
            if not key:
                logger.error(f"REVERSE FAILED: {field_name} - PII_ENC_KEY not found")
                return current_value
                
            fernet = Fernet(key.encode())
            encrypted_bytes = base64.b64decode(base64_data.encode())
            original_value = fernet.decrypt(encrypted_bytes).decode()
            return original_value
        except Exception as e:
            logger.error(f"REVERSE FAILED for {field_name}: {e}")
            return current_value
            
    return current_value
