<p align="center">
  <a href="https://pypi.org/project/rostaing-ocr/"><img src="https://img.shields.io/pypi/v/rostaing-ocr?color=blue&label=PyPI%20version" alt="PyPI version"></a>
  <a href="https://pypi.org/project/rostaing-ocr/"><img src="https://img.shields.io/pypi/pyversions/rostaing-ocr.svg" alt="Python versions"></a>
  <a href="https://github.com/Rostaing/rostaing-ocr/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/rostaing-ocr.svg" alt="License"></a>
  <a href="https://pepy.tech/project/rostaing-ocr"><img src="https://static.pepy.tech/badge/rostaing-ocr" alt="Downloads"></a>
</p>

# RostaingOCR

**Production-Grade Layout-Aware OCR for LLMs and RAG Systems**

`RostaingOCR` is a high-performance Python library designed to extract text from PDFs, Scanned PDFs, and images while **preserving complex layouts**. Unlike standard OCR tools that output a "soup" of words, this library uses **Deep Learning** and geometric reconstruction to maintain tables, columns, and document structure.

It is specifically optimized for **Retrieval-Augmented Generation (RAG)** pipelines where maintaining the visual structure of data (like invoice tables) is critical for LLM comprehension.

## Key Features

- **mj-layout-aware:** Uses geometric clustering to reconstruct tables and columns. Data stays on the correct line, visually aligned.
- **🧹 Noise Filtering:** Automatically detects and removes low-confidence text such as **messy handwriting, signatures, and stamps** to keep the output clean.
- **⚡ Local Processing:** Runs 100% locally (CPU or GPU). No external APIs, no data leaving your server.
- **📄 Universal Input:** Handles PDFs (digital & scanned) and common image formats via a robust Base64 architecture.
- **🔒 Privacy Focused:** Temporary files are handled securely and deleted immediately after extraction.

## Installation

```bash
pip install rostaing-ocr
```

<!-- ## Dependencies -->

<!-- This package relies on modern Deep Learning libraries:
- `python-doctr[torch]` (The OCR Engine) -->
<!-- - `pymupdf` (PDF rendering)
- `numpy` (Matrix operations) -->

*(Note: The first run will automatically download the necessary OCR models ~300MB)*

## Usage

### 1. Basic Usage (Default Behavior)
By default, the extractor prints the result to the console and saves it to `output.txt`.

```python
from rostaing_ocr import ocr_extractor

# This immediately runs the extraction using DocTR
extractor = ocr_extractor("documents/invoice.pdf")

# The extracted text is now in 'output.txt'
print(extractor) # Prints status summary (Time taken, pages processed)
```

### 2. Custom Output File
You can specify a different filename. The file will be created or overwritten automatically.

```python
from rostaing_ocr import ocr_extractor

extractor = ocr_extractor(
    "data/report.png",
    output_file="results/report_analysis.txt"
)
```

### 3. Silent Mode (Background Processing)
Useful for batch processing or server backends where you don't want console logs.

```python
from rostaing_ocr import ocr_extractor

extractor = ocr_extractor(
    "financial_statement.pdf",
    print_to_console=False,
    save_file=True
)
```

### 4. Direct Integration (RAG Pipelines)
Access the text variable directly without reading the file.

```python
from rostaing_ocr import ocr_extractor

extractor = ocr_extractor("scan.jpg", print_to_console=False)

if extractor.status == "Success":
    clean_text = extractor.extracted_text
    # Send 'clean_text' to GPT, Mistral, Gemini, Claude, Grok, Groq, Llama... or your Vector DB
```

## How It Works (Architecture)

1. **Input Normalization:** Converts PDF pages or Images into High-Res Base64 streams.
2. **Deep Learning Inference:** DBNet for detection + CRNN for recognition.
3. **Noise Filtering:** Scans confidence scores. Text with low confidence (e.g., `< 0.4`), such as signatures or stamps, is discarded.
4. **Geometric Reconstruction:**
   - Flattens the document hierarchy.
   - Clusters words into visual lines based on Y-axis alignment.
   - Calculates horizontal gaps to insert dynamic spacing (tabs vs spaces) to simulate columns.
5. **Output:** Returns a clean, structured string that looks like the original document.

## License

MIT License

## Useful Links
- [Author's LinkedIn](https://www.linkedin.com/in/davila-rostaing/)
- [Author's YouTube Channel](https://youtube.com/@RostaingAI?sub_confirmation=1)
- [GitHub Repository](https://github.com/Rostaing/rostaing-ocr)
- [PyPI Project Page](https://pypi.org/project/rostaing-ocr/)