"""
FastAPI application for OCR with EasyOCR.

Provides a simple REST API for performing OCR on uploaded images and PDFs
and generating searchable PDFs with embedded images.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, status
from fastapi.responses import JSONResponse
from PIL import Image
import numpy as np
import cv2
from app.make_pdf import make_searchable_pdf
from app.ocr_engine import OCREngine
from pydantic import BaseModel
from typing import List
import logging
import os
import base64
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import fitz  # PyMuPDF
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False
    logging.warning("PDF support not available. Install PyMuPDF.")

# Increase PIL image size limit to handle large scanned PDFs
from PIL import Image as PILImage
PILImage.MAX_IMAGE_PIXELS = 500000000  # 500 megapixels

app = FastAPI(
    title="EasyOCR API",
    description="High-accuracy OCR API with searchable PDF generation",
    version="1.0.0"
)

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.getLogger().setLevel(LOG_LEVEL)
logger = logging.getLogger("app")

# Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path} - Content-Type: {request.headers.get('content-type', 'N/A')}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.exception(f"Middleware caught exception: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Request processing error: {str(e)}"}
        )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# Lazily initialize OCR model on first request
ocr_model = None


class OCRBoxItem(BaseModel):
    """OCR result for a single text detection."""
    text: str
    confidence: float
    bbox: List[List[float]]  # [[x0,y0],[x1,y1],[x2,y2],[x3,y3]]


class OCRResponse(BaseModel):
    """Complete OCR response with results and searchable PDF."""
    ocr_result: List[OCRBoxItem]
    pdf_base64: str


@app.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    """Perform OCR on uploaded image or PDF."""
    logger.info(f"OCR request: {file.filename}")

    try:
        # Initialize OCR engine
        global ocr_model
        if ocr_model is None:
            logger.info("Initializing EasyOCR...")
            ocr_model = OCREngine()

        # Read file
        content = await file.read()
        logger.info(f"Read {len(content)} bytes")

        # Check if PDF
        is_pdf = file.filename and file.filename.lower().endswith('.pdf')

        # Helper function to process a single page
        def process_page(page_num, pdf_bytes):
            """Process a single PDF page and return results."""
            logger.info(f"Processing page {page_num + 1}...")
            
            # Open a separate PDF document for this thread
            thread_pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = thread_pdf_doc[page_num]
            
            # Get list of images on this page
            image_list = page.get_images(full=True)
            
            img = None
            page_results = []
            
            if image_list:
                logger.info(f"  Found {len(image_list)} embedded image(s) on page {page_num + 1}")
                
                # Process the largest image on the page
                images_with_size = []
                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]
                    try:
                        base_image = thread_pdf_doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        images_with_size.append((len(image_bytes), image_bytes, img_index))
                    except Exception as e:
                        logger.warning(f"  Could not extract image {img_index}: {e}")
                
                if images_with_size:
                    # Get the largest image (main page scan)
                    images_with_size.sort(reverse=True, key=lambda x: x[0])
                    largest_image_bytes = images_with_size[0][1]
                    
                    logger.info(f"  Using largest image ({images_with_size[0][0]} bytes)")
                    
                    # Extract and compress image
                    img = Image.open(BytesIO(largest_image_bytes)).convert("RGB")
                    original_size = img.size
                    logger.info(f"  Extracted image size: {original_size[0]}x{original_size[1]}")
                    
                    # Compress to JPEG quality 85
                    compressed_buf = BytesIO()
                    img.save(compressed_buf, format='JPEG', quality=85, optimize=True)
                    compressed_size = len(compressed_buf.getvalue())
                    logger.info(f"  Compressed from {images_with_size[0][0]} bytes to {compressed_size} bytes (quality=85)")
                    
                    # Reload the compressed image
                    compressed_buf.seek(0)
                    img = Image.open(compressed_buf)
                    img.load()
                    
                    # Run OCR on compressed image
                    img_array = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
                    result = ocr_model.ocr(img_array, cls=False)

                    for line in (result[0] if result and result[0] else []):
                        bbox, (text, confidence) = line
                        page_results.append({
                            "text": text,
                            "confidence": float(confidence),
                            "bbox": [[float(x), float(y)] for x, y in bbox]
                        })

                    logger.info(f"  Page {page_num + 1} OCR found {len(page_results)} text items")
            else:
                # No embedded images - fall back to rendering the page
                logger.info(f"  Page {page_num + 1} has no embedded images, rendering at 150 DPI...")
                mat = fitz.Matrix(150/72, 150/72)  # 150 DPI
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                img = Image.open(BytesIO(img_bytes)).convert("RGB")
                logger.info(f"  Rendered image size: {img.size[0]}x{img.size[1]}")
                
                # Run OCR
                img_array = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                result = ocr_model.ocr(img_array, cls=False)

                for line in (result[0] if result and result[0] else []):
                    bbox, (text, confidence) = line
                    page_results.append({
                        "text": text,
                        "confidence": float(confidence),
                        "bbox": [[float(x), float(y)] for x, y in bbox]
                    })

                logger.info(f"  Page {page_num + 1} OCR found {len(page_results)} text items")
            
            thread_pdf_doc.close()
            logger.info(f"  Page {page_num + 1} complete")
            
            return page_num, img, page_results

        # Process based on type
        if is_pdf and HAS_PDF_SUPPORT:
            logger.info("Processing PDF by extracting embedded images (parallel processing, 4 workers)...")
            # Open PDF document
            pdf_doc = fitz.open(stream=content, filetype="pdf")
            num_pages = len(pdf_doc)
            logger.info(f"PDF has {num_pages} pages - processing up to 4 pages in parallel")

            # Close the main PDF doc, we'll reopen it per thread
            pdf_doc.close()
            
            # Create output PDF document immediately
            doc_new = fitz.open()
            
            # Track results for response (indexed by page number)
            page_data = {}
            
            # Process pages in parallel with up to 4 workers
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Submit all pages for processing
                future_to_page = {
                    executor.submit(process_page, page_num, content): page_num 
                    for page_num in range(num_pages)
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        result_page_num, img, page_results = future.result()
                        page_data[result_page_num] = (img, page_results)
                        logger.info(f"Page {result_page_num + 1} processing completed")
                    except Exception as e:
                        logger.exception(f"Error processing page {page_num + 1}: {e}")
                        page_data[page_num] = (None, [])
            
            # Now build the PDF in page order and collect results
            all_results = []
            per_page_results = []
            
            for page_num in range(num_pages):
                img, page_results = page_data.get(page_num, (None, []))
                
                # Add this page to the output PDF
                if img:
                    img_width, img_height = img.size
                    
                    # Compress image to JPEG in memory
                    img_buf = BytesIO()
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    img.save(img_buf, format='JPEG', quality=85, optimize=True)
                    img_bytes = img_buf.getvalue()
                    logger.info(f"  Page {page_num + 1} compressed to {len(img_bytes)} bytes for PDF")
                    
                    # Convert image to PDF page using PyMuPDF
                    img_buf.seek(0)
                    img_doc = fitz.open(stream=img_bytes, filetype="jpeg")
                    rect = img_doc[0].rect
                    pdfbytes = img_doc.convert_to_pdf()
                    img_pdf = fitz.open("pdf", pdfbytes)
                    
                    # Create new page and insert image
                    new_page = doc_new.new_page(width=rect.width, height=rect.height)
                    new_page.show_pdf_page(rect, img_pdf, 0)
                    
                    # Add invisible text layer for searchability
                    for entry in page_results:
                        text = entry["text"]
                        bbox = entry["bbox"]
                        x0, y0 = bbox[0]
                        x2, y2 = bbox[2]
                        text_rect = fitz.Rect(x0, y0, x2, y2)
                        new_page.insert_textbox(
                            text_rect, text, fontsize=10,
                            color=(1, 1, 1), fill=(1, 1, 1),
                            render_mode=3, align=0
                        )
                    
                    img_doc.close()
                    img_pdf.close()
                    
                    # Release memory
                    del img, img_buf, img_bytes
                
                # Store results for response
                all_results.extend(page_results)
                per_page_results.append(page_results)
                
                logger.info(f"  Page {page_num + 1} added to final PDF")
            
            # Save the complete PDF
            logger.info(f"Saving final PDF with {num_pages} pages...")
            buf = BytesIO()
            doc_new.save(buf)
            doc_new.close()
            buf.seek(0)
            pdf_base64 = base64.b64encode(buf.read())
            
            logger.info(f"Success: {len(all_results)} OCR items from {num_pages} pages")
            return {
                "ocr_result": all_results,
                "ocr_result_per_page": per_page_results,
                "pdf_base64": pdf_base64.decode("utf-8"),
                "pages_processed": num_pages
            }
        else:
            # Single image processing
            logger.info("Processing single image...")
            img = Image.open(BytesIO(content)).convert("RGB")
            img_array = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            result = ocr_model.ocr(img_array, cls=False)

            page_results = []
            for line in (result[0] if result and result[0] else []):
                bbox, (text, confidence) = line
                page_results.append({
                    "text": text,
                    "confidence": float(confidence),
                    "bbox": [[float(x), float(y)] for x, y in bbox]
                })

            # Generate single-page PDF
            all_pages_data = [(img, page_results)]
            
            # Generate PDF with quality 85 compression
            logger.info(f"Generating single-page PDF...")
            pdf_base64 = make_searchable_pdf(all_pages_data, compress=True, quality=85)

            logger.info(f"Success: {len(page_results)} OCR items from single image")
            return {
                "ocr_result": page_results,
                "ocr_result_per_page": [page_results],
                "pdf_base64": pdf_base64.decode("utf-8"),
                "pages_processed": 1
            }

    except Exception as e:
        logger.exception("Error in OCR endpoint")
        return {"error": str(e)}

@app.get("/_health", tags=["health"])
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model": "EasyOCR",
        "device": ocr_model.device if ocr_model else "not_initialized"
    }


@app.get("/", tags=["info"])
def root():
    """API information."""
    return {
        "name": "EasyOCR API",
        "version": "1.0.0",
        "description": "High-accuracy OCR with searchable PDF generation",
        "docs": "/docs",
        "health": "/_health"
    }
