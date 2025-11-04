#!/usr/bin/env python3
import argparse
import base64
import json
import mimetypes
import os
import sys

import requests
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color
from io import BytesIO

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("Warning: PyMuPDF not installed. PDF detection will be limited.", file=sys.stderr)
    print("Install with: pip install PyMuPDF", file=sys.stderr)


def detect_pdf_type(pdf_path):
    """
    Detect PDF type: text-based, image-based (scanned), or mixed
    Returns: 'text', 'scanned', 'mixed', or 'empty'
    """
    if not HAS_PYMUPDF:
        return 'unknown'
    
    doc = fitz.open(pdf_path)
    
    has_text = False
    has_images = False
    total_chars = 0
    
    for page in doc:
        # Check for text
        text = page.get_text().strip()
        total_chars += len(text)
        if text:
            has_text = True
        
        # Check for images
        if page.get_images():
            has_images = True
    
    doc.close()
    
    # Determine type
    if has_images and not has_text:
        return 'scanned'  # Use OCR
    elif has_images and total_chars < 200:
        return 'scanned'  # Mostly images with minimal text
    elif has_text and not has_images:
        return 'text'  # Direct text extraction
    elif has_text and has_images:
        return 'mixed'  # Both available
    else:
        return 'empty'  # No content


def extract_text_from_pdf(pdf_path):
    """Extract text directly from a text-based PDF"""
    if not HAS_PYMUPDF:
        return ""
    
    doc = fitz.open(pdf_path)
    text_parts = []
    
    for page in doc:
        text_parts.append(page.get_text())
    
    doc.close()
    return "\n".join(text_parts)


def create_simple_pdf_from_text(text, output_path, original_pdf_path=None):
    """Create a simple PDF with extracted text"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Split text into paragraphs
    paragraphs = text.split('\n')
    
    for para in paragraphs:
        if para.strip():
            p = Paragraph(para.replace('<', '&lt;').replace('>', '&gt;'), styles['Normal'])
            story.append(p)
            story.append(Spacer(1, 12))
    
    doc.build(story)


def create_text_pdf_with_boxes(pdf_path, output_path):
    """Create a PDF with bounding boxes for text-based PDFs"""
    if not HAS_PYMUPDF:
        return
    
    doc = fitz.open(pdf_path)
    
    # Create new PDF with annotations
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Get text blocks with positions
        blocks = page.get_text("blocks")
        
        for block in blocks:
            x0, y0, x1, y1, text, block_no, block_type = block
            if block_type == 0:  # Text block
                # Draw rectangle around text
                rect = fitz.Rect(x0, y0, x1, y1)
                annot = page.add_rect_annot(rect)
                annot.set_colors(stroke=(1, 0, 0))  # Red
                annot.set_border(width=2)
                annot.update()
    
    doc.save(output_path)
    doc.close()


def create_pdf_with_boxes(image_path, ocr_result, output_path):
    """Create a PDF with bounding boxes drawn around recognized text using PyMuPDF."""
    # Open the original image
    img = Image.open(image_path).convert("RGB")
    img_width, img_height = img.size
    
    # Create a copy to draw bounding boxes on
    img_with_boxes = img.copy()
    draw = ImageDraw.Draw(img_with_boxes)
    
    # Draw bounding boxes for each detected text
    for item in ocr_result:
        bbox = item["bbox"]
        text = item["text"]
        confidence = item["confidence"]
        
        # Convert bbox to list of tuples for PIL
        points = [(x, y) for x, y in bbox]
        
        # Draw the bounding box (red color)
        draw.polygon(points, outline="red", width=3)
        
        # Optionally draw confidence score near the box
        x0, y0 = bbox[0]
        label = f"{confidence:.2f}"
        draw.text((x0, y0 - 15), label, fill="red")
    
    # Save image with boxes as JPEG quality=85 (following reference code)
    img_buf = BytesIO()
    img_with_boxes.save(img_buf, format='JPEG', quality=85, optimize=True)
    img_bytes = img_buf.getvalue()
    
    # Use PyMuPDF to create PDF (following reference code pattern)
    img_doc = fitz.open(stream=img_bytes, filetype="jpeg")
    rect = img_doc[0].rect
    pdfbytes = img_doc.convert_to_pdf()
    img_pdf = fitz.open("pdf", pdfbytes)
    
    # Create new PDF with the image
    doc_new = fitz.open()
    page = doc_new.new_page(width=rect.width, height=rect.height)
    page.show_pdf_page(rect, img_pdf, 0)
    
    # Save to output file
    doc_new.save(output_path)
    doc_new.close()
    img_doc.close()
    img_pdf.close()


def create_pdf_with_boxes_from_pdf(pdf_path, ocr_result, output_path, ocr_result_per_page=None):
    """Create a multi-page PDF with bounding boxes for OCR results using PyMuPDF.
    
    Args:
        pdf_path: Path to original PDF
        ocr_result: Flattened OCR results (backward compatibility)
        output_path: Where to save the boxed PDF
        ocr_result_per_page: Per-page OCR results from API (preferred)
    """
    if not HAS_PYMUPDF:
        print("Warning: PyMuPDF not available. Cannot create boxed PDF.", file=sys.stderr)
        return
    
    # Open original PDF to get page count
    pdf_doc = fitz.open(pdf_path)
    num_pages = len(pdf_doc)
    
    if num_pages == 0:
        print("Warning: PDF has no pages.", file=sys.stderr)
        pdf_doc.close()
        return
    
    print(f"Processing {num_pages} pages for boxed PDF...")
    
    # Create new output PDF
    doc_new = fitz.open()
    
    # Decide which approach to use
    if ocr_result_per_page and len(ocr_result_per_page) == num_pages:
        print(f"  Using per-page OCR results")
        use_per_page = True
    else:
        print(f"  Estimating OCR distribution across pages")
        use_per_page = False
        # Estimate OCR results per page (assuming even distribution)
        total_items = len(ocr_result)
        items_per_page = total_items // num_pages if num_pages > 0 else total_items
    
    for page_num in range(num_pages):
        print(f"  Processing page {page_num + 1}/{num_pages}...")
        page = pdf_doc[page_num]
        
        # Extract image from this page
        image_list = page.get_images(full=True)
        
        if image_list:
            # Extract the largest embedded image (main page scan)
            images_with_size = []
            for img_info in image_list:
                xref = img_info[0]
                try:
                    base_image = pdf_doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    images_with_size.append((len(image_bytes), image_bytes))
                except Exception as e:
                    continue
            
            if images_with_size:
                # Get largest image
                images_with_size.sort(reverse=True, key=lambda x: x[0])
                largest_image_bytes = images_with_size[0][1]
                img = Image.open(BytesIO(largest_image_bytes)).convert("RGB")
            else:
                # Fallback: render page at 150 DPI
                mat = fitz.Matrix(150/72, 150/72)
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                img = Image.open(BytesIO(img_bytes)).convert("RGB")
        else:
            # No embedded images - render page at 150 DPI
            mat = fitz.Matrix(150/72, 150/72)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            img = Image.open(BytesIO(img_bytes)).convert("RGB")
        
        img_width, img_height = img.size
        
        # Create a copy to draw bounding boxes on
        img_with_boxes = img.copy()
        draw = ImageDraw.Draw(img_with_boxes)
        
        # Get OCR results for this page
        if use_per_page:
            page_ocr_results = ocr_result_per_page[page_num]
        else:
            # Estimate which items belong to this page
            start_idx = page_num * items_per_page
            end_idx = start_idx + items_per_page if page_num < num_pages - 1 else total_items
            page_ocr_results = ocr_result[start_idx:end_idx]
        
        # Draw bounding boxes for each detected text on this page
        boxes_drawn = 0
        for item in page_ocr_results:
            bbox = item["bbox"]
            confidence = item["confidence"]
            
            # Convert bbox to list of tuples for PIL
            points = [(x, y) for x, y in bbox]
            
            # Draw the bounding box (red color)
            draw.polygon(points, outline="red", width=3)
            
            # Draw confidence score near the box
            x0, y0 = bbox[0]
            label = f"{confidence:.2f}"
            draw.text((x0, y0 - 15), label, fill="red")
            boxes_drawn += 1
        
        print(f"    Drew {boxes_drawn} bounding boxes on page {page_num + 1}")
        
        # Save image with boxes as JPEG quality=85
        img_buf = BytesIO()
        img_with_boxes.save(img_buf, format='JPEG', quality=85, optimize=True)
        img_bytes = img_buf.getvalue()
        
        # Use PyMuPDF to create page and add to output PDF
        img_doc = fitz.open(stream=img_bytes, filetype="jpeg")
        rect = img_doc[0].rect
        pdfbytes = img_doc.convert_to_pdf()
        img_pdf = fitz.open("pdf", pdfbytes)
        
        # Add new page to output PDF
        new_page = doc_new.new_page(width=rect.width, height=rect.height)
        new_page.show_pdf_page(rect, img_pdf, 0)
        
        img_doc.close()
        img_pdf.close()
    
    pdf_doc.close()
    
    # Save the complete multi-page PDF
    doc_new.save(output_path)
    doc_new.close()
    print(f"Saved {num_pages}-page boxed PDF to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Call the OCR API and save the searchable PDF")
    parser.add_argument("image_path", help="Path to the input image or PDF (jpg/png/pdf)")
    parser.add_argument("--url", default="http://127.0.0.1:3600", help="Base URL of the API (default: http://127.0.0.1:3600)")
    parser.add_argument("--out", default=None, help="Where to write the resulting PDF (default: <input_name>.pdf)")
    parser.add_argument("--json", default=None, help="Where to write the JSON output (default: <input_name>.json)")
    parser.add_argument("--boxed", default=None, help="Where to write the PDF with bounding boxes (default: <input_name>_boxed.pdf)")
    parser.add_argument("--text", default=None, help="Where to write the plain text output (default: <input_name>.txt)")
    parser.add_argument("--force-ocr", action="store_true", help="Force OCR even for text-based PDFs")
    parser.add_argument("--timeout", type=int, default=600, help="Request timeout in seconds (default: 600)")
    args = parser.parse_args()

    if not os.path.exists(args.image_path):
        print(f"File not found: {args.image_path}", file=sys.stderr)
        sys.exit(2)

    # Generate default output filenames based on input filename
    input_base = os.path.splitext(args.image_path)[0]
    if args.out is None:
        args.out = f"{input_base}_ocr.pdf"
    if args.json is None:
        args.json = f"{input_base}.json"
    if args.boxed is None:
        args.boxed = f"{input_base}_boxed.pdf"
    if args.text is None:
        args.text = f"{input_base}.txt"

    # Check if input is a PDF
    is_pdf = args.image_path.lower().endswith('.pdf')
    
    if is_pdf and not args.force_ocr:
        print("Analyzing PDF...")
        pdf_type = detect_pdf_type(args.image_path)
        print(f"PDF type detected: {pdf_type}")
        
        if pdf_type == 'text':
            # Extract text directly without OCR
            print("Extracting text directly from PDF (no OCR needed)...")
            text = extract_text_from_pdf(args.image_path)
            
            # Save plain text output
            with open(args.text, "w", encoding="utf-8") as text_f:
                text_f.write(text)
            print(f"Saved plain text output to {args.text}")
            
            # Create a simple PDF
            create_simple_pdf_from_text(text, args.out, args.image_path)
            print(f"Saved PDF to {args.out}")
            
            # Create PDF with text boxes
            create_text_pdf_with_boxes(args.image_path, args.boxed)
            print(f"Saved PDF with bounding boxes to {args.boxed}")
            
            # Create JSON output
            json_data = {
                "method": "direct_extraction",
                "pdf_type": pdf_type,
                "text": text,
                "char_count": len(text)
            }
            with open(args.json, "w") as json_f:
                json.dump(json_data, json_f, indent=2)
            print(f"Saved JSON output to {args.json}")
            
            print("\n✅ Text extraction complete (no OCR required)")
            return
        
        elif pdf_type == 'mixed':
            print("PDF contains both text and images.")
            
            # Extract existing text for reference only
            existing_text = extract_text_from_pdf(args.image_path)
            
            # Save existing text to a separate file (just for reference)
            existing_text_file = f"{input_base}_extracted_text.txt"
            with open(existing_text_file, "w", encoding="utf-8") as text_f:
                text_f.write(existing_text)
            print(f"Dumped existing text to {existing_text_file} (for reference)")
            
            # Continue to OCR processing for complete results
            print("Sending PDF to OCR engine for complete text extraction...")
        
        elif pdf_type == 'scanned':
            print("PDF contains scanned images. Proceeding with OCR...")
        elif pdf_type == 'unknown':
            print("Cannot determine PDF type. Proceeding with OCR...")
    
    # For images or scanned PDFs, call the OCR API
    mime, _ = mimetypes.guess_type(args.image_path)
    if not mime:
        if is_pdf:
            mime = "application/pdf"
        else:
            mime = "image/jpeg"

    print(f"Sending file to OCR API (timeout: {args.timeout}s)...")
    with open(args.image_path, "rb") as f:
        files = {"file": (os.path.basename(args.image_path), f, mime)}
        resp = requests.post(f"{args.url}/ocr", files=files, timeout=args.timeout)

    if not resp.ok:
        print(f"Request failed: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    b64_pdf = data.get("pdf_base64")
    if not b64_pdf:
        print("Response missing pdf_base64", file=sys.stderr)
        sys.exit(1)

    # Save the original searchable PDF
    with open(args.out, "wb") as out_f:
        out_f.write(base64.b64decode(b64_pdf))

    ocr_result = data.get("ocr_result", [])
    ocr_result_per_page = data.get("ocr_result_per_page")  # NEW: Per-page results
    ocr_items = len(ocr_result)
    print(f"Saved {args.out} (OCR items: {ocr_items})")
    
    # Save the JSON output
    with open(args.json, "w") as json_f:
        json.dump(data, json_f, indent=2)
    print(f"Saved JSON output to {args.json}")
    
    # Save plain text output
    with open(args.text, "w", encoding="utf-8") as text_f:
        for item in ocr_result:
            text_f.write(item["text"] + "\n")
    print(f"Saved plain text output to {args.text}")
    
    # Create PDF with bounding boxes
    if ocr_result:
        if is_pdf:
            create_pdf_with_boxes_from_pdf(args.image_path, ocr_result, args.boxed, ocr_result_per_page)
            print(f"Saved PDF with bounding boxes to {args.boxed}")
        else:
            create_pdf_with_boxes(args.image_path, ocr_result, args.boxed)
            print(f"Saved PDF with bounding boxes to {args.boxed}")


if __name__ == "__main__":
    main()
