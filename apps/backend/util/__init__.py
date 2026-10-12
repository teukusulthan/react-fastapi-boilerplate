"""Reusable, framework-light utilities.

- ``util.helper``  — ids, UTC time, case conversion, PII masking
- ``util.crypto``  — AES-256-GCM payload crypto and Fernet field encryption
- ``util.s3``      — lazily created boto3 S3 client (AWS / MinIO / Supabase Storage)
- ``util.kafka``   — lazily created Kafka producer singleton (optional)
"""
