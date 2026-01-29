# PTM-OCR

Batch OCR Processing for Thai Documents using Typhoon OCR API

## Installation

```bash
pip install ptm-ocr
```

## Quick Start

### 1. Set Environment Variables

Create a `.env` file or export environment variables:

```bash
export OCR_BASE_URL=https://api.opentyphoon.ai/v1
export OCR_API_KEY=your_api_key_here
export OCR_MODEL=typhoon-ocr-7b
```

### 2. Run OCR

**Command Line:**

```bash
# Basic usage
ptm-ocr data/pdfs

# With options
ptm-ocr data/pdfs -o output -w 8 -t structure
```

**Python API:**

```python
from ptm_ocr import process_folder, process_pdf_file

# Process entire folder
summary = process_folder(
    input_folder="data/pdfs",
    output_folder="output",
    task_type="default",
    max_workers=4
)

# Process single PDF
summary = process_pdf_file(
    pdf_path="document.pdf",
    output_path="document.jsonl"
)
```

## CLI Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `output` | Output folder for JSONL files |
| `--task-type` | `-t` | `default` | OCR task type: `default` or `structure` |
| `--workers` | `-w` | `4` | Number of parallel workers |
| `--base-url` | | env | Override OCR_BASE_URL |
| `--api-key` | | env | Override OCR_API_KEY |
| `--model` | | env | Override OCR_MODEL |

## Output Format (JSONL)

Each line in the output file is a JSON object:

```json
{"page": 1, "text": "ข้อความที่ OCR ได้", "status": "success", "error": null}
{"page": 2, "text": "ข้อความหน้า 2", "status": "success", "error": null}
```

## Task Types

- **default**: General documents, infographics
- **structure**: Complex layouts (tables, forms, mixed content)

## Reading Output

```python
import json

with open('output/document.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        page = json.loads(line)
        print(f"Page {page['page']}: {page['text'][:100]}...")
```

## License

MIT
