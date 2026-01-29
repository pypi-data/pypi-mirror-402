#!/usr/bin/env python3
"""
Token Generator with Reversible Encryption
Generates encrypted tokens that can be decrypted back to original values
"""

import hashlib
import base64
from cryptography.fernet import Fernet
import os

import logging
from ..config.settings import settings

logger = logging.getLogger(__name__)

class TokenGenerator:
    """Generate reversible encrypted tokens for PII fields."""
    
    def __init__(self, prefix="TKN", token_size=8):
        self.prefix = prefix
        self.token_size = token_size
        
        # Get encryption key from environment
        self.encryption_key = settings.PII_ENC_KEY
        if not self.encryption_key:
            raise ValueError("PII_ENC_KEY not found in environment")
        
        # Initialize Fernet cipher
        self.cipher = Fernet(self.encryption_key.encode())
    
    def generate_token(self, table_name, record_data):
        """Generate a simple hash-based token (for record-level tokens)."""
        # Create a deterministic hash for record-level identification
        seed_input = f"{table_name}:{str(sorted(record_data.items()))}"
        hash_value = hashlib.md5(seed_input.encode(), usedforsecurity=False).hexdigest()[:self.token_size]
        return f"{self.prefix}_{hash_value}"
    
    def generate_encrypted_token(self, original_value):
        """Generate reversible encrypted token from original value.
        
        Args:
            original_value: The original PII value to encrypt
            
        Returns:
            Encrypted token that can be decrypted back to original
        """
        if not original_value:
            return None
        
        try:
            # Encrypt the original value
            encrypted_bytes = self.cipher.encrypt(str(original_value).encode())
            
            # Convert to base64 and create token
            encrypted_b64 = base64.urlsafe_b64encode(encrypted_bytes).decode()
            
            # Create token with prefix
            token = f"{self.prefix}_{encrypted_b64}"
            
            return token
            
        except Exception as e:
            logger.error(f"Error generating encrypted token: {e}")
            return None
    
    def decrypt_token(self, encrypted_token):
        """Decrypt token back to original value.
        
        Args:
            encrypted_token: The encrypted token to decrypt
            
        Returns:
            Original value or None if decryption fails
        """
        if not encrypted_token or not encrypted_token.startswith(f"{self.prefix}_"):
            return None
        
        try:
            # Remove prefix
            encrypted_b64 = encrypted_token[len(f"{self.prefix}_"):]
            
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_b64.encode())
            
            # Decrypt to original value
            original_bytes = self.cipher.decrypt(encrypted_bytes)
            original_value = original_bytes.decode()
            
            return original_value
            
        except Exception:
            #print(f"Error decrypting token: {e}")
            return None