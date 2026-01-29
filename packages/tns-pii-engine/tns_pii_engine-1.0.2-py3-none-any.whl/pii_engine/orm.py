import json
import logging
from typing import Any, Optional
from pii_engine.wrappers.integration_wrappers import reverse_pii_fields, process_pii_fields

logger = logging.getLogger(__name__)


class PIIProperty:
    """Descriptor that transparently unmasks a PII field using the model's TOKEN_SET."""
    def __init__(self, table_name: str, field_name: str):
        self.table_name = table_name
        self.field_name = field_name
        self.private_name = f"_{field_name}"

    def __get__(self, instance, owner):
        if instance is None:
            return getattr(owner, self.private_name)
        
        masked_value = getattr(instance, self.private_name)
        token_set = getattr(instance, "TOKEN_SET", None)
        
        if masked_value is None:
            return None
            
        return reverse_pii_fields(self.table_name, self.field_name, masked_value, token_set)

    def __set__(self, instance, value):
        setattr(instance, self.private_name, value)

class PIIUrlProperty(PIIProperty):
    """Descriptor that unmasks a PII field and then generates a presigned S3 URL."""
    _signer = None # Callback function to sign URLs (e.g. S3 presigner)
    
    @classmethod
    def set_signer(cls, signer_func):
        """Register a URL signer function."""
        cls._signer = signer_func

    def __get__(self, instance, owner):
        if instance is None:
            return self
            
        unmasked_url = super().__get__(instance, owner)
        if not unmasked_url or not unmasked_url.strip():
            return None
        
        # 1. Use registered signer if available
        if self._signer:
            return self._signer(unmasked_url)
            
        # 2. Standalone Signer Logic (using engine settings)
        return self._sign_url(unmasked_url)

    def _sign_url(self, s3_url: str) -> str:
        """Sign S3 URL using engine's standalone settings."""
        from .config.settings import settings
        from urllib.parse import urlparse
        
        # If no bucket configured, return as is
        if not settings.AWS_S3_BUCKET:
            return s3_url
            
        try:
            import boto3
            # Extract key
            parsed = urlparse(s3_url)
            key = parsed.path.lstrip("/")
            
            # Session/Client
            s3_client = boto3.client(
                "s3",
                region_name=settings.AWS_REGION or "us-east-1"
            )
            
            return s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": settings.AWS_S3_BUCKET, "Key": key},
                ExpiresIn=3600,
            )
        except Exception:
            # Fallback for current app integration if boto3 fails or key missing
            try:
                from app.utils.s3_utils import generate_presigned_url_from_s3_url
                return generate_presigned_url_from_s3_url(s3_url)
            except Exception:
                return s3_url

class PIIBase:
    """Mixin to provide model-level PII masking and update logic."""
    def update_pii(self, data: dict):
        """
        Processes PII fields and updates the model.
        Automatically merges TOKEN_SET to prevent data loss.
        """
        table_name = getattr(self, "__tablename__", None)
        if not table_name:
            raise ValueError("Model must have __tablename__ to use update_pii")

        # Process new data for PII
        processed = process_pii_fields(table_name, "pseudo", None, data)
        
        # Merge TokenSet with existing TOKEN_SET
        existing_tokens = {}
        current_token_set_json = getattr(self, "TOKEN_SET", None)
        if current_token_set_json and current_token_set_json.strip():
            try:
                existing_tokens = json.loads(current_token_set_json)
                if isinstance(existing_tokens, str):  # Handle double encoding
                    existing_tokens = json.loads(existing_tokens)
            except Exception:
                logger.warning(f"Failed to parse existing TOKEN_SET for model {table_name}")
                existing_tokens = {}

        new_tokens = processed.get("TokenSet", {})
        existing_tokens.update(new_tokens)
        
        # Store merged tokens
        self.TOKEN_SET = json.dumps(existing_tokens, ensure_ascii=False)

        # Update model attributes
        field_data = processed.get("fields", {})
        for field, value in field_data.items():
            # Try setting private underscore version first
            private_attr = f"_{field}"
            if hasattr(self, private_attr):
                setattr(self, private_attr, value)
            elif hasattr(self, field):
                # Fallback to direct attribute if no underscore version exists
                setattr(self, field, value)
