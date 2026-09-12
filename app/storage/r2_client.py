import os
import io
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger("r2_client")

_s3_client = None

def get_s3_client():
    global _s3_client
    if _s3_client is None:
        if (
            settings.ENVIRONMENT.lower() == "production"
            and settings.CLOUDFLARE_R2_ACCOUNT_ID
            and settings.CLOUDFLARE_R2_ACCESS_KEY_ID
            and settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY
        ):
            import boto3
            from botocore.config import Config
            endpoint = f"https://{settings.CLOUDFLARE_R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
            s3_config = Config(
                retries={'max_attempts': 1},
                connect_timeout=3,
                read_timeout=5
            )
            _s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
                region_name="auto",
                config=s3_config
            )
            logger.info("Connected to Cloudflare R2 client")
        else:
            logger.info("Using local static storage for DPR reports (set ENVIRONMENT=production to use R2).")
            _s3_client = False
    return _s3_client

def upload_dpr_pdf(pdf_bytes: bytes, filename: str) -> str:
    """
    Upload generated DPR PDF to Cloudflare R2 (zero egress fees).
    Falls back to local static directory if R2 is unconfigured.
    Returns public download URL.
    """
    client = get_s3_client()
    object_key = f"dpr_reports/{filename}"

    if client and client is not False:
        try:
            client.put_object(
                Bucket=settings.CLOUDFLARE_R2_BUCKET_NAME,
                Key=object_key,
                Body=pdf_bytes,
                ContentType="application/pdf",
            )
            public_url = f"{settings.CLOUDFLARE_R2_PUBLIC_URL}/{object_key}"
            logger.info(f"Uploaded DPR PDF to Cloudflare R2: {public_url}")
            return public_url
        except Exception as e:
            logger.error(f"Failed to upload to Cloudflare R2: {e}. Falling back to local static storage.")

    # Local fallback
    local_dir = os.path.join(os.getcwd(), "static", "dprs")
    os.makedirs(local_dir, exist_ok=True)
    local_filepath = os.path.join(local_dir, filename)
    with open(local_filepath, "wb") as f:
        f.write(pdf_bytes)

    local_url = f"{settings.BACKEND_INTERNAL_URL}/static/dprs/{filename}"
    logger.info(f"Saved DPR PDF locally at {local_filepath}, public URL: {local_url}")
    return local_url

def get_public_url(filename: str) -> str:
    """Get public URL for an uploaded file."""
    if settings.CLOUDFLARE_R2_PUBLIC_URL and settings.CLOUDFLARE_R2_ACCOUNT_ID:
        return f"{settings.CLOUDFLARE_R2_PUBLIC_URL}/dpr_reports/{filename}"
    return f"{settings.BACKEND_INTERNAL_URL}/static/dprs/{filename}"
