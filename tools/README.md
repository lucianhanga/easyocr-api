# Tools Directory# Tools Directory



This directory contains utility scripts for the EasyOCR API project.This directory contains utility scripts for the EasyOCR API project.



## Scripts## Scripts



### `setup_venv.sh`### `setup_venv.sh`

**Unified setup script** - Creates and configures the virtual environment with your choice of dependencies.**Unified setup script** - Creates and configures the virtual environment with your choice of dependencies.



```bash```bash

# Run from project root# Run from project root

./tools/setup_venv.sh./tools/setup_venv.sh

``````



**Setup Options:****Setup Options:**

1. **Full server setup** - Complete EasyOCR API server (~4GB download)1. **Full server setup** - Complete EasyOCR API server (~4GB download)

   - FastAPI, EasyOCR, PyTorch, CUDA support   - FastAPI, EasyOCR, PyTorch, CUDA support

   - Can run the API server locally   - Can run the API server locally

   - Includes all client tools   - Includes all client tools



2. **Client-only setup** - Lightweight client tools only (~50MB download)2. **Client-only setup** - Lightweight client tools only (~50MB download)

   - Requests, Pillow, PyMuPDF, ReportLab   - Requests, Pillow, PyMuPDF, ReportLab

   - Perfect for using client tools with remote server   - Perfect for using client tools with remote server

   - No AI/ML dependencies   - No AI/ML dependencies



**Features:****Features:**

- ✅ Interactive setup type selection- ✅ Interactive setup type selection

- ✅ Python version validation (requires 3.8+)- ✅ Python version validation (requires 3.8+)

- ✅ Handles existing venv (asks to recreate or keep)- ✅ Handles existing venv (asks to recreate or keep)

- ✅ Colored output for better readability- ✅ Colored output for better readability

- ✅ Error handling and validation- ✅ Error handling and validation

- ✅ Different verification steps per setup type- ✅ Different verification steps per setup type



### `activate_venv.sh`### `activate_venv.sh`

**Quick activation helper** - Activates the virtual environment.**Quick activation helper** - Activates the virtual environment.



```bash```bash

# Source it to activate in current shell# Source it to activate in current shell

source ./tools/activate_venv.shsource ./tools/activate_venv.sh



# Or use directly# Or use directly

source ./venv/bin/activatesource ./venv/bin/activate

``````



### `ocr_client.py`### `ocr_client.py`

**OCR testing client** - Tests the API with files.**OCR testing client** - Tests the API with files.



```bash```bash

# After activating venv# After activating venv

./tools/ocr_client.py /path/to/your/file.pdf./tools/ocr_client.py /path/to/your/file.pdf

./tools/ocr_client.py /path/to/your/image.png./tools/ocr_client.py /path/to/your/image.png

``````



## Quick Start## Quick Start



### Option 1: Client Tools Only (Lightweight)### Option 1: Client Tools Only (Lightweight)

**Best for:** Connecting to remote OCR server, minimal dependencies**Best for:** Connecting to remote OCR server, minimal dependencies



```bash```bash

# Setup lightweight client environment# Setup lightweight client environment

./tools/setup_venv.sh./tools/setup_venv.sh

# Choose option 2 (client-only)# Choose option 2 (client-only)



# Activate environment# Activate environment

source ./venv/bin/activatesource ./venv/bin/activate



# Test with remote server# Test with remote server

./tools/ocr_client.py your_document.pdf --url http://your-server:3600./tools/ocr_client.py your_document.pdf --url http://your-server:3600

``````



### Option 2: Full Server + Client Setup### Option 2: Full Server + Client Setup

**Best for:** Running OCR server locally, complete setup**Best for:** Running OCR server locally, complete setup



```bash```bash

# Setup full environment# Setup full environment

./tools/setup_venv.sh./tools/setup_venv.sh

# Choose option 1 (full server)# Choose option 1 (full server)



# Activate environment# Activate environment

source ./venv/bin/activatesource ./venv/bin/activate



# Start the API server# Start the API server

uvicorn app.main:app --host 0.0.0.0 --port 3600uvicorn app.main:app --host 0.0.0.0 --port 3600



# Test with client (in another terminal)# Test with client (in another terminal)

source ./venv/bin/activatesource ./venv/bin/activate

./tools/ocr_client.py your_document.pdf./tools/ocr_client.py your_document.pdf

``````



## Requirements## Requirements



- Python 3.8+- Python 3.8+

- Virtual environment support (`python3 -m venv`)- Virtual environment support (`python3 -m venv`)

- Internet connection (for package installation)- Internet connection (for package installation)



## Troubleshooting## Troubleshooting



### "python3 not found"### "python3 not found"

```bash```bash

# Ubuntu/Debian# Ubuntu/Debian

sudo apt-get update && sudo apt-get install python3 python3-venv python3-pipsudo apt-get update && sudo apt-get install python3 python3-venv python3-pip



# CentOS/RHEL# CentOS/RHEL

sudo yum install python3 python3-pipsudo yum install python3 python3-pip

``````



### "pip install fails"### "pip install fails"

```bash```bash

# Upgrade pip first# Upgrade pip first

pip install --upgrade pippip install --upgrade pip



# Or use system package manager# Or use system package manager

sudo apt-get install python3-dev  # Ubuntu/Debiansudo apt-get install python3-dev  # Ubuntu/Debian

``````



### "Virtual environment activation fails"### "Virtual environment activation fails"

```bash```bash

# Make sure to source the script# Make sure to source the script

source ./venv/bin/activatesource ./venv/bin/activate



# Not just run it# Not just run it

./venv/bin/activate  # ❌ Wrong./venv/bin/activate  # ❌ Wrong

``````



## Dependencies Comparison## Dependencies Comparison



| Component | Full Setup | Client-Only || Component | Full Setup | Client-Only |

|-----------|------------|-------------||-----------|------------|-------------|

| FastAPI | ✅ | ❌ || FastAPI | ✅ | ❌ |

| EasyOCR | ✅ | ❌ || EasyOCR | ✅ | ❌ |

| PyTorch | ✅ | ❌ || PyTorch | ✅ | ❌ |

| CUDA Support | ✅ | ❌ || CUDA Support | ✅ | ❌ |

| Requests | ✅ | ✅ || Requests | ✅ | ✅ |

| Pillow | ✅ | ✅ || Pillow | ✅ | ✅ |

| PyMuPDF | ✅ | ✅ || PyMuPDF | ✅ | ✅ |

| ReportLab | ✅ | ✅ || ReportLab | ✅ | ✅ |

| **Download Size** | ~4GB | ~50MB || **Download Size** | ~4GB | ~50MB |

| **Use Case** | Local server | Remote client || **Use Case** | Local server | Remote client |



## Docker Alternative## Docker Alternative



If you prefer Docker over virtual environments, see `DOCKER_SETUP.md` for containerized deployment options.If you prefer Docker over virtual environments, see `DOCKER_SETUP.md` for containerized deployment options.