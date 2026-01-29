"""
PII Engine - Enterprise PII Masking, Tokenization & Encryption Module

A reusable module for handling PII data across all endpoints and applications.
"""


from .orm import PIIProperty, PIIUrlProperty, PIIBase
from .config.settings import settings

def configure(**kwargs):
    """Entry point to configure PII engine as a module."""
    settings.configure(**kwargs)

__version__ = "1.0.0"
__author__ = "PII Platform Team"