"""
rostaing-ocr: Deep Learning Layout-Aware OCR
Features:
- 100% Local (CPU/GPU).
- No .exe dependencies.
- Uses Base64 architecture for image handling.
- Uses DocTR (ResNet+Transformer) for smart block detection.
- **Layout-Aware**: Reconstructs tables by analyzing word geometry.

Dependencies:
    pip install python-doctr[torch] pymupdf
"""

import os
import sys
import time
import base64
import warnings
import json
from pathlib import Path
from typing import List, Any

# ============================================================
# LIBRARY SETUP
# ============================================================
warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

try:
    import fitz  # PyMuPDF
    from doctr.io import DocumentFile
    from doctr.models import ocr_predictor
    import torch
except ImportError as e:
    raise ImportError(f"Missing dependency: {e}. Run: pip install python-doctr[torch] pymupdf")

# ============================================================
# CORE CLASS
# ============================================================

class ocr_extractor:
    def __init__(
        self, 
        file_path: str, 
        output_file: str = "output.txt", 
        print_to_console: bool = False,
        save_file: bool = True
    ):
        self.file_path = Path(file_path).resolve()
        self.output_path = Path(output_file).resolve()
        self.print_to_console = print_to_console
        self.save_file = save_file
        
        self.extracted_text = ""
        self.processing_time = 0.0
        self.status = "Pending"

        # Initialize RostaingOCR Model (Deep Learning)
        print("Loading RostaingOCR...", file=sys.stderr) # (Deep Learning Model)
        
        # Check for GPU
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Running on: {self.device}", file=sys.stderr)
        
        try:
            # We use the default model (DBNet + CRNN) which is excellent for documents
            self.model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
            if torch.cuda.is_available():
                self.model.cuda()
        except Exception as e:
            self.status = "Model Load Error"
            print(f"Error loading model: {e}", file=sys.stderr)
            return

        try:
            self._pipeline()
        except Exception as e:
            self.status = "Error"
            print(f"Critical Error: {e}", file=sys.stderr)

    def _pipeline(self):
        start_time = time.time()
        
        if not self.file_path.exists():
            print(f"File not found: {self.file_path}", file=sys.stderr)
            return

        try:
            # 1. Conversion to Base64 (Your requested architecture)
            base64_pages = []
            ext = self.file_path.suffix.lower()
            
            if ext == '.pdf':
                base64_pages = self._pdf_to_base64_list()
            elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                base64_pages = [self._image_to_base64(self.file_path)]
            else:
                raise ValueError(f"Unsupported format: {ext}")

            # 2. OCR Processing via DocTR (from Base64 data)
            full_text_pages = []
            
            for i, b64_data in enumerate(base64_pages):
                page_text = self._process_base64_with_doctr(b64_data)
                full_text_pages.append(f"--- Page {i + 1} ---\n{page_text}")

            self.extracted_text = "\n\n".join(full_text_pages)

            # 3. Save
            if self.save_file:
                with open(self.output_path, 'w', encoding='utf-8') as f:
                    f.write(self.extracted_text)

            # 4. Print
            if self.print_to_console:
                print(self.extracted_text)

            self.status = "Success"

        finally:
            self.processing_time = time.time() - start_time

    def _pdf_to_base64_list(self) -> List[str]:
        """Convert PDF pages to High-Res Base64."""
        b64_list = []
        doc = fitz.open(self.file_path)
        try:
            # Zoom x2 is usually enough for DocTR
            mat = fitz.Matrix(2, 2)
            for page in doc:
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_bytes = pix.tobytes("png")
                b64_str = base64.b64encode(img_bytes).decode('utf-8')
                b64_list.append(b64_str)
        finally:
            doc.close()
        return b64_list

    def _image_to_base64(self, path: Path) -> str:
        """Read image to Base64."""
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def _process_base64_with_doctr(self, b64_string: str) -> str:
        """
        Decodes Base64 and runs Deep Learning OCR.
        
        LAYOUT-AWARE LOGIC:
        Instead of iterating by Blocks (which breaks tables), this function:
        1. Flattens all words.
        2. Sorts them by Y-coordinate.
        3. Clusters them into visual lines based on vertical alignment.
        4. Reconstructs horizontal spacing.
        """
        # Decode Base64 back to bytes
        image_bytes = base64.b64decode(b64_string)
        
        # DocTR expects a list of images (bytes)
        doc = DocumentFile.from_images(image_bytes)
        
        # Inference
        result = self.model(doc)
        
        page = result.pages[0]
        
        # 1. Extract all words with their geometry
        all_words = []
        for block in page.blocks:
            for line in block.lines:
                for word in line.words:
                    # geometry is ((xmin, ymin), (xmax, ymax))
                    xmin, ymin = word.geometry[0]
                    xmax, ymax = word.geometry[1]
                    center_y = (ymin + ymax) / 2
                    height = ymax - ymin
                    
                    all_words.append({
                        'text': word.value,
                        'xmin': xmin,
                        'xmax': xmax,
                        'cy': center_y,
                        'height': height
                    })

        if not all_words:
            return ""

        # 2. Sort all words by vertical position (Top to Bottom)
        all_words.sort(key=lambda w: w['cy'])

        # 3. Cluster words into visual lines
        lines = []
        current_line = []
        
        if all_words:
            current_line = [all_words[0]]

        for word in all_words[1:]:
            last_word = current_line[-1]
            
            # Check vertical distance to see if it's the same line
            # Threshold: 50% of the word height
            dist = abs(word['cy'] - last_word['cy'])
            avg_h = (word['height'] + last_word['height']) / 2
            
            if dist < (avg_h * 0.5):
                current_line.append(word)
            else:
                lines.append(current_line)
                current_line = [word]
        
        if current_line:
            lines.append(current_line)

        # 4. Construct Output String with Table Spacing
        output_str = []
        
        for line in lines:
            # Sort words in line from Left to Right
            line.sort(key=lambda w: w['xmin'])
            
            line_text = ""
            last_x_end = 0
            
            for word in line:
                if last_x_end == 0:
                    line_text += word['text']
                else:
                    gap = word['xmin'] - last_x_end
                    
                    # Logic for spacing:
                    # > 0.1 (10% of page width) -> Big Tab (Column separator)
                    # > 0.02 (2% of page width) -> Space
                    if gap > 0.1:
                        line_text += " \t   " + word['text'] 
                    elif gap > 0.02:
                        line_text += " " + word['text']
                    else:
                        line_text += " " + word['text']

                last_x_end = word['xmax']
            
            output_str.append(line_text)
            
        return "\n".join(output_str)

    def __str__(self):
        return f"RostaingOCR Extraction Complete | Time: {self.processing_time:.2f}s | Output: {self.output_path}"

# ============================================================
# EXECUTION
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rostaing_ocr.py <file_path>")
    else:
        extractor = ocr_extractor(
            sys.argv[1], 
            print_to_console=False, 
            save_file=True
        )
        print(str(extractor), file=sys.stderr)