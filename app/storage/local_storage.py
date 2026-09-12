import os
import logging
from app.config import settings

logger = logging.getLogger("local_storage")

def save_dpr_pdf(pdf_bytes: bytes, filename: str) -> str:
    """
    Save generated DPR PDF directly to local static storage.
    Returns the accessible relative URL (/static/dprs/...) for the report.
    """
    local_dir = os.path.join(os.getcwd(), "static", "dprs")
    os.makedirs(local_dir, exist_ok=True)
    local_filepath = os.path.join(local_dir, filename)
    with open(local_filepath, "wb") as f:
        f.write(pdf_bytes)

    # Return relative URL so frontend/browser requests resolve to current host
    local_url = f"/static/dprs/{filename}"
    logger.info(f"Saved DPR PDF locally at {local_filepath}, public URL: {local_url}")
    return local_url

# Alias for backward compatibility
upload_dpr_pdf = save_dpr_pdf

def get_public_url(filename: str) -> str:
    """Get URL for a saved DPR file."""
    return f"/static/dprs/{filename}"
