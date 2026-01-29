#!/usr/bin/env python3
"""
Phase 2 Wrapper Function: Reverse PII Data Lookup
Takes TokenSet + fields and returns original data
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

def reverse_pii_fields(table_name: str, _record_id: int, token_data: dict) -> dict:
    """
    Phase 2: Reverse lookup - Convert TokenSet back to original data
    
    Args:
        table_name: Database table name ("jobseekers" or "employers")
        record_id: User ID 
        token_data: TokenSet + fields data from Phase 1
        
    Returns:
        Dict with original PII data
    """
    from ..core.clean_processor import PIIProcessor
        
    # Extract TokenSet and fields from input data
    token_set = token_data.get('TokenSet', {})
    fields_data = token_data.get('fields', {})
    
    if not token_set:
        raise ValueError("TokenSet is required for reverse lookup")
    
    pii_processor = PIIProcessor()
    original_data = {}
    
    # Process each field in the data
    for field_name, field_value in fields_data.items():
        # Check if this field has a token (meaning it was PII processed)
        token_value = token_set.get(field_name)
        
        if token_value and isinstance(token_value, str) and token_value.startswith('EE_'):
            # This is a PII field with token - retrieve original data using token
            try:
                # Use the token to retrieve original data from vault
                original_value = pii_processor.vault.retrieve_field_from_main_table(
                    table_name, field_name, token_value, field_value
                )
                if original_value and not original_value.startswith('[ORIGINAL_DATA_FOR_'):
                    original_data[field_name] = original_value
                else:
                    # If no original data found, keep pseudonymized value
                    original_data[field_name] = field_value
            except Exception as e:
                # If retrieval fails, keep the pseudonymized value
                logger.error(f"REVERSE FAILED for {field_name}: {e}")
                original_data[field_name] = field_value
        else:
            # Non-PII field - keep original value from TokenSet or fields
            original_data[field_name] = token_value if token_value else field_value
    
    return original_data