# PDF Support

The EasyOCR API now supports intelligent PDF processing with automatic detection of PDF content type.

## Features

### Automatic PDF Detection

The client automatically detects whether a PDF contains:
- **Text-based PDFs**: PDFs with selectable text (no OCR needed)
- **Scanned PDFs**: PDFs containing only images (requires OCR)
- **Mixed PDFs**: PDFs with both text and images

### Smart Processing

1. **Text-based PDFs** - Text is extracted directly without OCR (fast, accurate)
2. **Scanned PDFs** - Automatically sent to OCR engine for text recognition
3. **Multi-page PDFs** - All pages are processed and combined into results

## Usage

### Basic Usage (Automatic Detection)

```bash
# Process a PDF - automatically detects if OCR is needed
python examples/ocr_client.py document.pdf

# Output files:
# - document.pdf (searchable PDF)
# - document.json (JSON with OCR results)
# - document.txt (plain text)
# - document_boxed.pdf (PDF with bounding boxes, for text PDFs)
```

### Force OCR on Text PDFs

```bash
# Force OCR even if PDF contains text
python examples/ocr_client.py document.pdf --force-ocr
```

### Process Images (Original Functionality)

```bash
# Process images as before
python examples/ocr_client.py image.jpg
python examples/ocr_client.py image.png
```

## API Changes

### Multi-Page PDF Support

The API now processes multi-page PDFs:

```bash
# Send a multi-page PDF to the API
curl -X POST http://localhost:3600/ocr \
  -F "file=@document.pdf" \
  -o response.json
```

**Response includes:**
- Combined OCR results from all pages
- Searchable PDF output
- Text and confidence scores for each detected text block

## Installation

### Install PDF Dependencies

```bash
# Install Python packages
pip install PyMuPDF>=1.23.0 pdf2image>=1.16.0

# Install system dependencies (Linux/Ubuntu)
sudo apt-get install poppler-utils

# Install system dependencies (macOS)
brew install poppler
```

### Docker

The Docker image includes all PDF dependencies:

```bash
# Build with PDF support
docker build -t easyocr-api .

# Run
docker run -p 3600:3600 easyocr-api
```

## Examples

### Text-based PDF

```bash
$ python examples/ocr_client.py invoice.pdf

Analyzing PDF...
PDF type detected: text
Extracting text directly from PDF (no OCR needed)...
Saved plain text output to invoice.txt
Saved PDF to invoice.pdf
Saved PDF with bounding boxes to invoice_boxed.pdf
Saved JSON output to invoice.json

✅ Text extraction complete (no OCR required)
```

### Scanned PDF

```bash
$ python examples/ocr_client.py scanned_document.pdf

Analyzing PDF...
PDF type detected: scanned
PDF contains scanned images. Proceeding with OCR...
Sending file to OCR API...
Processing PDF file...
Converted PDF to 3 images in 2.14s
Processing page 1/3...
Page 1 OCR completed: lines=42 in 8.53s
Processing page 2/3...
Page 2 OCR completed: lines=38 in 7.92s
Processing page 3/3...
Page 3 OCR completed: lines=35 in 8.11s
Saved scanned_document.pdf (OCR items: 115)
Saved JSON output to scanned_document.json
Saved plain text output to scanned_document.txt
```

### Mixed Content PDF

```bash
$ python examples/ocr_client.py report.pdf

Analyzing PDF...
PDF type detected: mixed
Extracting text directly from PDF (no OCR needed)...
Saved plain text output to report.txt
Saved PDF to report.pdf
Saved PDF with bounding boxes to report_boxed.pdf
Saved JSON output to report.json

✅ Text extraction complete (no OCR required)
```

## Performance

### Processing Times (typical)

| Document Type | Pages | Method | Time |
|--------------|-------|--------|------|
| Text PDF | 1 | Direct extraction | < 1s |
| Text PDF | 10 | Direct extraction | 1-2s |
| Scanned PDF | 1 | OCR | 8-12s (CPU) / 2-3s (GPU) |
| Scanned PDF | 10 | OCR | 80-120s (CPU) / 20-30s (GPU) |

## Troubleshooting

### PyMuPDF Not Found

```bash
pip install PyMuPDF
```

### pdf2image Not Found

```bash
pip install pdf2image

# Also install poppler
# Ubuntu/Debian: sudo apt-get install poppler-utils
# macOS: brew install poppler
```

### PDF Processing Fails

Check that poppler-utils is installed:

```bash
# Test poppler
pdftoppm -v
```

## API Endpoints

### POST /ocr

**Accepts:**
- Images: JPG, PNG, BMP, TIFF
- PDFs: Single or multi-page

**Returns:**
```json
{
  "ocr_result": [
    {
      "text": "Sample text",
      "confidence": 0.98,
      "bbox": [[x0, y0], [x1, y1], [x2, y2], [x3, y3]]
    }
  ],
  "pdf_base64": "base64_encoded_pdf..."
}
```

## Best Practices

1. **Use automatic detection** - Let the client decide if OCR is needed
2. **For text PDFs** - Direct extraction is 10-50x faster than OCR
3. **For scanned PDFs** - Use GPU for better performance
4. **Large multi-page PDFs** - Consider processing in batches or using async

## Limitations

- Multi-page PDF output currently uses first page dimensions
- Very large PDFs (100+ pages) may timeout
- OCR quality depends on scan quality (300 DPI recommended)
