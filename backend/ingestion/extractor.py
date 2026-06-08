"""
Enhanced PDF extraction using Docling for semantic document parsing.

Features:
- Semantic block detection (headings, paragraphs, lists, tables, images)
- Never splits numbered lists or procedures
- Converts tables to natural language
- Extracts images and generates descriptions with Gemini
- Preserves complete metadata for retrieval
"""

import logging
from typing import List, Optional
from pathlib import Path
import base64
import io

# Lazy imports - only import when needed to avoid loading transformers at module init
# from docling.document_converter import DocumentConverter, PdfFormatOption
# from docling.datamodel.base_models import InputFormat
# from docling.datamodel.pipeline_options import PdfPipelineOptions

from models.schemas import ExtractedBlock
from google import genai
from google.genai import types
from config import config

logger = logging.getLogger(__name__)

# Initialize client for image descriptions
_client = None

def _get_client():
    """Get or create singleton client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GOOGLE_API_KEY)
    return _client


def _generate_image_description(image_data: bytes, caption: str = "") -> str:
    """
    Generate detailed textual description of an image using Gemini 2.5 Flash.
    
    Args:
        image_data: Raw image bytes
        caption: Optional caption from document
    
    Returns:
        Detailed description suitable for retrieval
    """
    try:
        client = _get_client()
        
        # Create prompt for technical diagram/image description
        prompt = f"""You are analyzing a technical diagram or image from an industrial maintenance manual.

{"Caption: " + caption if caption else ""}

Provide a detailed, structured description that includes:
1. Main subject/equipment shown
2. Key components and their labels
3. Important measurements, ratings, or specifications visible
4. Any warnings, cautions, or safety information
5. Relationship between components if showing assembly/system

Make the description searchable - use terminology that engineers would use when looking for this information.
Be factual and precise. Focus on technical details."""

        # Generate description with image
        response = client.models.generate_content(
            model=config.LLM_MODEL,
            contents=[prompt, {"mime_type": "image/jpeg", "data": image_data}]
        )
        description = response.text.strip()
        
        logger.info(f"Generated image description: {description[:100]}...")
        return description
        
    except Exception as e:
        logger.error(f"Failed to generate image description: {e}")
        return f"Image: {caption}" if caption else "Technical diagram (description unavailable)"


def extract_blocks(file_path: str, doc_id: str, doc_name: str, equipment_tag: str) -> List[ExtractedBlock]:
    """
    Extract semantic blocks from PDF using Docling.
    
    Args:
        file_path: Path to the PDF file
        doc_id: UUID for this document
        doc_name: Original filename
        equipment_tag: Equipment identifier
    
    Returns:
        List of ExtractedBlock objects with semantic structure preserved
    """
    blocks: List[ExtractedBlock] = []
    
    try:
        # LAZY IMPORT: Only import Docling when actually needed
        # This prevents transformers from loading at module import time
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        
        logger.info(f"[Docling] Importing Docling libraries...")
        
        # Configure Docling pipeline
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True  # Enable OCR for scanned documents
        pipeline_options.do_table_structure = True  # Parse table structure
        
        # Initialize converter
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        logger.info(f"[Docling] Converting {doc_name}...")
        result = converter.convert(file_path)
        doc = result.document
        
        current_heading = ""
        page_number = 1
        
        # Iterate through document structure
        for item in doc.iterate_items():
            item_type = type(item).__name__
            
            # Extract text and metadata
            text = item.text.strip() if hasattr(item, 'text') else ""
            if not text:
                continue
            
            # Get page number if available
            if hasattr(item, 'prov') and hasattr(item.prov[0], 'page_no'):
                page_number = item.prov[0].page_no
            
            # Get bounding box if available
            bbox = (0, 0, 0, 0)
            if hasattr(item, 'prov') and hasattr(item.prov[0], 'bbox'):
                bbox_obj = item.prov[0].bbox
                bbox = (bbox_obj.l, bbox_obj.t, bbox_obj.r, bbox_obj.b)
            
            # Classify block type based on Docling structure
            block_type = "paragraph"  # default
            
            if item_type == "DoclingHeading":
                block_type = "heading"
                current_heading = text
                
            elif item_type == "DoclingList":
                # Numbered or bullet list - keep as single block
                block_type = "list"
                
            elif item_type == "DoclingTable":
                # Table - will be converted to prose
                block_type = "table"
                
            elif item_type == "DoclingPicture" or item_type == "DoclingFigure":
                block_type = "figure"
                
                # Try to extract image and generate description
                try:
                    if hasattr(item, 'image'):
                        image_data = item.image.pil_image
                        if image_data:
                            # Convert PIL image to bytes
                            img_byte_arr = io.BytesIO()
                            image_data.save(img_byte_arr, format='JPEG')
                            img_bytes = img_byte_arr.getvalue()
                            
                            # Generate description
                            caption = item.caption if hasattr(item, 'caption') else ""
                            description = _generate_image_description(img_bytes, caption)
                            text = description
                except Exception as e:
                    logger.warning(f"Failed to process image on page {page_number}: {e}")
                    if hasattr(item, 'caption') and item.caption:
                        text = f"Figure: {item.caption}"
                        
            elif item_type == "DoclingCaption":
                block_type = "figure_caption"
            
            # Create ExtractedBlock
            blocks.append(ExtractedBlock(
                doc_id=doc_id,
                doc_name=doc_name,
                equipment_tag=equipment_tag,
                block_type=block_type,
                text=text,
                page_number=page_number,
                bbox=bbox,
                font_size=12.0,  # Docling doesn't provide font size
                is_bold=False,   # Docling doesn't provide font styling
                section_heading=current_heading if block_type != "heading" else "",
            ))
        
        logger.info(f"[Docling] Extracted {len(blocks)} semantic blocks from {doc_name}")
        return blocks
        
    except Exception as e:
        logger.error(f"[Docling] Extraction failed for {file_path}: {e}")
        logger.info("[Docling] Falling back to PyMuPDF extractor...")
        
        # Fallback to old PyMuPDF extractor
        from ingestion.extractor_legacy import extract_blocks_pymupdf
        return extract_blocks_pymupdf(file_path, doc_id, doc_name, equipment_tag)
