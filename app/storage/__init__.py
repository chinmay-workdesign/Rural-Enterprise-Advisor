"""Storage package for generated reports and documents."""
from .local_storage import save_dpr_pdf, upload_dpr_pdf, get_public_url

__all__ = [
    "save_dpr_pdf",
    "upload_dpr_pdf",
    "get_public_url",
]
