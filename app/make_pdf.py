from io import BytesIO
import base64
from PIL import Image as PILImage
import logging
import fitz  # PyMuPDF for efficient JPEG handling

logger = logging.getLogger(__name__)


def make_searchable_pdf(pages_data, compress=True, quality=85):
    """
    Creates a searchable multi-page PDF (image + invisible text) using PyMuPDF.
    Following the reference code pattern for better JPEG compression.

    Args:
        pages_data: Either:
            - Single page: (pil_image, ocr_data) tuple or dict
            - Multi-page: List of (pil_image, ocr_data) tuples
        compress: Whether to compress images (default True)
        quality: JPEG quality for compression (default 85)

    Returns:
        Base64-encoded PDF bytes
    """
    # Normalize input to list of (image, ocr_data) tuples
    if isinstance(pages_data, (tuple, list)) and len(pages_data) == 2:
        # Check if it's a single (image, ocr_data) tuple
        if hasattr(pages_data[0], 'size'):  # First element is a PIL image
            pages_data = [pages_data]
        # Otherwise assume it's already a list of tuples

    # Handle legacy single-page call: make_searchable_pdf(image, ocr_data)
    if not isinstance(pages_data, list):
        raise ValueError("pages_data must be a list of (image, ocr_data) tuples")

    # Create a new empty PDF using PyMuPDF (following reference code pattern)
    doc_new = fitz.open()

    for page_num, page_data in enumerate(pages_data):
        logger.info(f"Processing page {page_num + 1}/{len(pages_data)} for PDF")
        pil_image, ocr_data = page_data
        img_width, img_height = pil_image.size
        logger.info(f"Page {page_num + 1} size: {img_width}x{img_height}, OCR items: {len(ocr_data)}")

        # Compress image to JPEG in memory
        img_buf = BytesIO()
        
        # Ensure RGB mode for JPEG
        if pil_image.mode in ('RGBA', 'LA', 'P'):
            pil_image = pil_image.convert('RGB')
        elif pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Save as JPEG with quality=85 (following reference code)
        pil_image.save(img_buf, format='JPEG', quality=quality, optimize=True)
        img_bytes = img_buf.getvalue()
        
        compressed_size = len(img_bytes)
        logger.info(f"  Image compressed to {compressed_size} bytes for PDF embedding")
        
        # Following reference code pattern: convert image to PDF page using PyMuPDF
        img_buf.seek(0)
        img_doc = fitz.open(stream=img_bytes, filetype="jpeg")
        rect = img_doc[0].rect
        pdfbytes = img_doc.convert_to_pdf()
        img_pdf = fitz.open("pdf", pdfbytes)
        
        # Create a new page in the output PDF and insert the image-PDF content
        page = doc_new.new_page(width=rect.width, height=rect.height)
        page.show_pdf_page(rect, img_pdf, 0)
        
        # Add invisible text layer for searchability
        for entry in ocr_data:
            # Handle both dict and Pydantic model
            if hasattr(entry, 'text'):
                text = entry.text
                bbox = entry.bbox
            else:
                text = entry["text"]
                bbox = entry["bbox"]
            
            # Get bounding box coordinates
            x0, y0 = bbox[0]
            x2, y2 = bbox[2]
            
            # Create invisible text annotation at OCR position
            # Note: PyMuPDF coordinates are from top-left, similar to OCR
            text_rect = fitz.Rect(x0, y0, x2, y2)
            
            # Insert invisible text (render_mode=3 means invisible)
            page.insert_textbox(
                text_rect,
                text,
                fontsize=10,
                color=(1, 1, 1),  # White text
                fill=(1, 1, 1),   # White fill
                render_mode=3,    # Invisible (neither fill nor stroke)
                align=0           # Left align
            )
        
        img_doc.close()
        img_pdf.close()

    # Save to BytesIO buffer
    buf = BytesIO()
    doc_new.save(buf)
    doc_new.close()
    
    buf.seek(0)
    encoded = base64.b64encode(buf.read())
    return encoded
