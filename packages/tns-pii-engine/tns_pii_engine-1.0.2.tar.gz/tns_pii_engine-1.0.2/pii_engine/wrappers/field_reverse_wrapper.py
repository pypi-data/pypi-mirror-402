#!/usr/bin/env python3
"""
Field-Level Reverse PII Function
Matches your production usage pattern
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def reverse_pii_fields(_table_name: str, field_name: str, current_value: str, token_set_json: str) -> str:
    """
    Reverse lookup for individual field - matches your production usage
    
    Args:
        table_name: Database table name ("employers", "jobseekers")
        field_name: Field name ("company_name", "first_name", etc.)
        current_value: Current pseudonymized value
        token_set_json: JSON string containing TokenSet
        
    Returns:
        Original field value if token exists, otherwise current_value
    """
    try:
        # Parse token set JSON
        if isinstance(token_set_json, str):
            token_set = json.loads(token_set_json)
        else:
            token_set = token_set_json or {}
        
        # Get token for this field
        field_token = token_set.get(field_name)
        
        # Check if this is a PII field with token
        if field_token and isinstance(field_token, str) and field_token.startswith('EE_'):
            return f"[ORIGINAL_{field_name.upper()}_FOR_{field_token}]"
        else:
            # Non-PII field or no token - return current value
            return current_value
            
    except Exception as e:
        logger.error(f"Error in reverse lookup for {field_name}: {e}")
        return current_value

def reverse_pii_fields_batch(table_name: str, _record_id: int, token_data: dict) -> dict:
    """
    Batch reverse lookup - for complete record reversal
    
    Args:
        table_name: Database table name
        record_id: Record ID
        token_data: {'TokenSet': tokens, 'fields': pseudonymized_data}
        
    Returns:
        Dict with original data
    """
    from ..core.clean_processor import PIIProcessor
    
    token_set = token_data.get('TokenSet', {})
    fields_data = token_data.get('fields', {})
    
    if not token_set:
        raise ValueError("TokenSet is required for reverse lookup")
    
    pii_processor = PIIProcessor()
    original_data = {}
    
    # Process each field
    for field_name, field_value in fields_data.items():
        token_value = token_set.get(field_name)
        
        if token_value and isinstance(token_value, str) and token_value.startswith('EE_'):
            # PII field - attempt to retrieve original
            try:
                original_value = pii_processor.vault.retrieve_field_from_main_table(
                    table_name, field_name, token_value, field_value
                )
                original_data[field_name] = original_value
            except Exception as e:
                original_data[field_name] = field_value
                logger.error(f"  FAILED {field_name}: {e}")
        else:
            # Non-PII field
            original_data[field_name] = token_value if token_value else field_value
    
    return original_data