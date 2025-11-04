# Contributing to EasyOCR API

Thank you for considering contributing to this project!

## Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd easyocr-api
   ```

2. **Set up development environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the development server**

   ```bash
   ./run.sh
   # Or manually:
   uvicorn app.main:app --reload --port 8000
   ```

## Making Changes

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Keep functions focused and single-purpose

## Testing

Before submitting a PR:

1. Test with sample images
2. Verify Docker build works: `docker build -t easyocr-api .`
3. Check health endpoint: `curl http://localhost:8000/_health`
4. Test OCR endpoint with various image types

## Questions?

Open an issue for discussion before making major changes.
