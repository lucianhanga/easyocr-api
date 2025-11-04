#!/usr/bin/env python3
"""
Generate a sample test image with text for OCR testing.
"""
from PIL import Image, ImageDraw, ImageFont
import sys


def create_test_image(filename="test_image.png"):
    """Create a test image with various text styles."""

    # Create a white background image
    width, height = 800, 600
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # Try to use a nice font, fall back to default if not available
    try:
        # Try common font paths
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        try:
            # Linux font paths
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            # Fall back to default font
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
            print("Warning: Using default font (limited size). Install TrueType fonts for better results.")

    # Draw various text samples
    y_position = 50

    # Title
    draw.text((50, y_position), "OCR Test Document", fill='black', font=font_large)
    y_position += 80

    # Regular text
    draw.text((50, y_position), "This is a sample document for testing OCR.",
              fill='black', font=font_medium)
    y_position += 60

    # Numbers
    draw.text((50, y_position), "Invoice #12345 - Amount: €1,234.56",
              fill='black', font=font_medium)
    y_position += 60

    # Mixed languages (European)
    draw.text((50, y_position), "English • Français • Deutsch • Español",
              fill='blue', font=font_small)
    y_position += 50

    # More text
    draw.text((50, y_position), "Date: November 2, 2025",
              fill='black', font=font_small)
    y_position += 50

    # Small print
    draw.text((50, y_position), "This document contains multiple text sizes and styles.",
              fill='gray', font=font_small)
    y_position += 80

    # Box with text
    box_x, box_y = 50, y_position
    box_width, box_height = 700, 100
    draw.rectangle([box_x, box_y, box_x + box_width, box_y + box_height],
                   outline='black', width=2)
    draw.text((box_x + 20, box_y + 30),
              "Testing bounding box detection and text extraction.",
              fill='black', font=font_medium)

    # Save the image
    image.save(filename)
    print(f"✅ Test image created: {filename}")
    print(f"   Size: {width}x{height} pixels")
    return filename


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "test_image.png"
    create_test_image(filename)
