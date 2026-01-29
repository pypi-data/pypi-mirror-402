#!/usr/bin/env python3
"""
Internal Settings for PII Engine
"""

import os

class PIISettings:
    def __init__(self):
        # encryption Key used for Fernet tokens (EE_... or TKN_...)
        self.PII_ENC_KEY = os.getenv("PII_ENC_KEY", "")
        
        # AWS S3 Settings for URL presigning (optional)
        self.AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    def configure(self, pii_enc_key=None, aws_s3_bucket=None, aws_region=None):
        """Manually configure PII engine settings."""
        if pii_enc_key:
            self.PII_ENC_KEY = pii_enc_key
        if aws_s3_bucket:
            self.AWS_S3_BUCKET = aws_s3_bucket
        if aws_region:
            self.AWS_REGION = aws_region

settings = PIISettings()
