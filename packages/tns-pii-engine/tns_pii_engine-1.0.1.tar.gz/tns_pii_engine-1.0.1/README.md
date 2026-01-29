# PII Engine

A stateless, high-performance, and standalone PII (Personally Identifiable Information) processing module designed for SQLAlchemy models.

## Features

- **Transparent PII**: Access PII fields on your models as if they were plain text. The engine handles unmasking on-the-fly.
- **Stateless Architecture**: No database dependencies. All encryption and pseudonymization are performed in-memory.
- **Model-Level Integration**: Easy-to-use mixins and descriptors for SQLAlchemy.
- **Centralized Configuration**: Configure the engine once at application startup.
- **Auto-Presigned URLs**: Automatically generates S3 presigned URLs for PII fields containing S3 paths.

---

## 1. Quick Setup

Configure the engine in your main application entry point (e.g., `main.py`).

```python
import pii_engine

pii_engine.configure(
    pii_enc_key="your-encryption-key",
    aws_s3_bucket="your-bucket-name",
    aws_region="us-east-1"
)
```

---

## 2. Model Integration

Use `PIIBase` mixin and `PIIProperty`/`PIIUrlProperty` descriptors to make your models "Transparent".

### Define your Model

```python
from sqlalchemy import Column, String, Text
from pii_engine import PIIBase, PIIProperty, PIIUrlProperty
from your_app.database import Base

class Employer(Base, PIIBase):
    __tablename__ = "employers"
    
    # Internal columns (prefixed with _)
    _first_name = Column("first_name", String(100))
    _resume_url = Column("resume_url", String(255))
    
    # This stores the encryption tokens for the row
    TOKEN_SET = Column(Text) 

    # Transparent PII Properties
    first_name = PIIProperty("employers", "first_name")
    resume_url = PIIUrlProperty("employers", "resume_url")
```

---

## 3. Usage

### Saving Data (Masking)
The `update_pii` method handles masking and token generation automatically. It merges new tokens with existing ones to prevent data loss.

```python
employer = Employer()
data = {"first_name": "John Doe", "resume_url": "s3://bucket/resumes/john.pdf"}

# This masks data and sets TOKEN_SET
employer.update_pii(data) 
db.add(employer)
db.commit()
```

### Retrieving Data (Unmasking)
Just access the attributes directly.

```python
# Returns "John Doe" (unmasked)
print(employer.first_name) 

# Returns a signed S3 URL
print(employer.resume_url) 
```

---

## 4. Configuration Options

The `configure()` method accepts the following parameters:

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `pii_enc_key` | `env:PII_ENC_KEY` | Key used for Fernet encryption. |
| `aws_s3_bucket` | `env:AWS_S3_BUCKET` | S3 bucket for URL signing. |
| `aws_region` | `us-east-1` | AWS region for S3 client. |

---

## Architecture Note

This engine is designed to be **Stateless**. Unlike older versions, it does not require a `pii_vault` database table. All reversal information is stored within the model's own `TOKEN_SET` column using reversible encryption.
