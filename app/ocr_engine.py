"""
EasyOCR Engine with hardware detection and optimization.

Provides high-accuracy OCR with automatic CUDA/CPU detection.
Supports European multilingual text (printed and handwritten).
"""
import logging
from typing import List
import numpy as np

logger = logging.getLogger(__name__)


class OCREngine:
    """
    Hardware-aware OCR engine using EasyOCR with HuggingFace models.

    Auto-detects and optimizes for available hardware (CUDA GPU or CPU).
    Returns results in standardized format with bounding boxes.
    """

    def __init__(self, languages=None, quantize: bool = False):
        """
        Initialize OCR engine with hardware detection.

        Args:
            languages: List of language codes (default: European languages)
            quantize: Whether to use quantized models (faster, slightly less accurate)
        """
        if languages is None:
            # Default: European languages (Latin-based)
            languages = ['en', 'fr', 'de', 'es', 'it', 'pt']

        self.languages = languages
        self.quantize = quantize
        self.reader = None
        self.device = self._detect_hardware()

        logger.info(
            f"Initializing OCR engine: languages={languages}, device={self.device}, "
            f"quantize={quantize}"
        )

    def _detect_hardware(self) -> str:
        """
        Detect available hardware acceleration.

        Returns:
            "cuda" if NVIDIA GPU available, otherwise "cpu"
        """
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"CUDA GPU detected: {gpu_name}")
                return "cuda"
        except ImportError:
            logger.warning("PyTorch not available, cannot check CUDA")
        except Exception as e:
            logger.warning(f"Error detecting CUDA: {e}")

        logger.info("Using CPU for inference")
        return "cpu"

    def _lazy_init(self):
        """Lazy initialization of EasyOCR reader on first use."""
        if self.reader is not None:
            return

        try:
            import easyocr
        except ImportError:
            raise ImportError(
                "EasyOCR not installed. Install with: pip install easyocr"
            )

        use_gpu = (self.device == "cuda")

        logger.info(f"Loading EasyOCR with languages={self.languages}, gpu={use_gpu}")

        # Initialize EasyOCR reader with CRAFT detector (most accurate)
        self.reader = easyocr.Reader(
            self.languages,
            gpu=use_gpu,
            quantize=self.quantize,
            verbose=False,
        )
        logger.info("EasyOCR reader initialized successfully")

    def ocr(
        self,
        image: np.ndarray,
        cls: bool = False
    ) -> List[List]:
        """
        Perform OCR on image.

        Args:
            image: BGR numpy array (OpenCV format)
            cls: Unused parameter for compatibility

        Returns:
            List of [
                [bbox, (text, confidence)]
            ]
            where bbox = [[x0,y0], [x1,y1], [x2,y2], [x3,y3]] (4 corner points)
        """
        self._lazy_init()

        # EasyOCR expects RGB, convert from BGR if needed
        import cv2
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Run OCR with detailed output
        # Returns: [([[x0,y0], [x1,y1], [x2,y2], [x3,y3]], text, confidence), ...]
        # Tuned parameters for better text grouping and recognition:
        # - width_ths: Horizontal distance threshold for merging boxes (default 0.5)
        # - height_ths: Vertical distance threshold (default 0.5)
        # - add_margin: Extra margin around detected text (default 0.1)
        results = self.reader.readtext(
            image_rgb,
            detail=1,  # Return bounding boxes
            paragraph=False,  # Don't merge lines into paragraphs
            width_ths=1.0,  # Increase horizontal merging threshold for better word grouping
            add_margin=0.15,  # Slightly more margin to capture complete characters
        )

        # Convert EasyOCR format to standardized format
        # EasyOCR: (bbox, text, confidence)
        # Our format: [bbox, (text, confidence)]
        formatted_results = []
        for bbox, text, confidence in results:
            # bbox is already in the correct format [[x0,y0], [x1,y1], [x2,y2], [x3,y3]]
            formatted_results.append([bbox, (text, confidence)])

        # Wrap in list for consistency
        return [formatted_results]
