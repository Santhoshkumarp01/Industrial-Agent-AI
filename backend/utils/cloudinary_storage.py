"""
Cloudinary storage integration for persistent PDF storage.
Free tier: 25GB storage, no credit card required.
"""

import os
import logging
from pathlib import Path
import cloudinary
import cloudinary.uploader
import cloudinary.api

logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)


def upload_pdf(file_path: str, doc_id: str) -> str:
    """
    Upload PDF to Cloudinary and return the public URL.
    
    Args:
        file_path: Local path to PDF file
        doc_id: Unique document ID
    
    Returns:
        Public URL of the uploaded PDF
    """
    try:
        logger.info(f"Uploading PDF to Cloudinary: {doc_id}")
        
        result = cloudinary.uploader.upload(
            file_path,
            public_id=f"maintenance_pdfs/{doc_id}",
            resource_type="raw",  # For non-image files
            folder="industrial-agent-ai",
            overwrite=True,
            invalidate=True
        )
        
        pdf_url = result["secure_url"]
        logger.info(f"PDF uploaded successfully: {pdf_url}")
        return pdf_url
        
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise


def delete_pdf(doc_id: str) -> bool:
    """
    Delete PDF from Cloudinary.
    
    Args:
        doc_id: Document ID
    
    Returns:
        True if successful
    """
    try:
        cloudinary.uploader.destroy(
            f"maintenance_pdfs/{doc_id}",
            resource_type="raw"
        )
        logger.info(f"Deleted PDF from Cloudinary: {doc_id}")
        return True
    except Exception as e:
        logger.error(f"Cloudinary delete failed: {e}")
        return False


def get_pdf_url(doc_id: str) -> str:
    """
    Get direct URL to PDF from Cloudinary.
    
    Args:
        doc_id: Document ID
    
    Returns:
        Public URL
    """
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    return f"https://res.cloudinary.com/{cloud_name}/raw/upload/industrial-agent-ai/maintenance_pdfs/{doc_id}.pdf"
