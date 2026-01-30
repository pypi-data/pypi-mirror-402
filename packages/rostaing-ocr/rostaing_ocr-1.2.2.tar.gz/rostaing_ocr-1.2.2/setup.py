from setuptools import setup, find_packages
import os

# Robust way to read the README file
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rostaing-ocr",
    version="1.2.2",  # INCREMENTED VERSION (Mandatory for PyPI update)
    author="Davila Rostaing",
    author_email="rostaingdavila@gmail.com",
    description="High-Precision OCR Extraction for LLMs and RAG Systems: PDFs, Scanned PDFs, and Images",
    long_description=long_description,
    long_description_content_type="text/markdown", # Crucial for PyPI to render MD
    url="https://github.com/Rostaing/rostaing-ocr", # Optionnel
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Graphics :: Capture :: Scanners",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Intended Audience :: Developers",
    ],
    python_requires='>=3.8',
    install_requires=[
        "pymupdf>=1.20.0",
        "python-doctr[torch]>=0.7.0",
        "pillow>=9.0.0",
        "numpy>=1.21.0",
    ],
    # This ensures files in MANIFEST.in are included
    include_package_data=True, 
)