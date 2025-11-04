#!/bin/bash
# Test script to demonstrate automatic image resizing feature

echo "=== OCR Client - Image Resizing Test ==="
echo ""

# Activate virtual environment
source venv/bin/activate

echo "1. Testing with small image (test.png - should not resize)"
echo "-----------------------------------------------------------"
python3 ./tools/ocr_client.py ~/Desktop/test/test.png --timeout 120 2>&1 | grep -E "(Resizing|Image size|Sending)"
echo ""

echo "2. Testing with large image (test5.png - should resize to 1400px)"
echo "--------------------------------------------------------------------"
python3 ./tools/ocr_client.py ~/Desktop/test/test5.png --max-size 1400 --timeout 300 --out /tmp/test5_ocr.pdf --json /tmp/test5_ocr.json --text /tmp/test5_ocr.txt 2>&1 | grep -E "(Resizing|Image size|Sending|Saved|Total|Empty)"
echo ""

if [ -f "/tmp/test5_ocr.json" ]; then
    echo "3. Analyzing OCR results"
    echo "------------------------"
    python3 << 'EOF'
import json
with open('/tmp/test5_ocr.json') as f:
    data = json.load(f)
    results = data['ocr_result']
    empty = sum(1 for r in results if r['text'] == '')
    print(f"Total detections: {len(results)}")
    print(f"Empty detections: {empty}")
    print(f"First 10 texts:")
    for i, r in enumerate(results[:10]):
        print(f"  {i+1}. \"{r['text'][:50]}\" (conf: {r['confidence']:.3f})")
EOF
fi

echo ""
echo "=== Test Complete ===" 
