from setuptools import setup, find_packages

# Read README for long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "Extract text, images, and tables from PDF files with analysis"

setup(
    name="pdfcoordex",
    version="0.1.1",
    author="Your Name",
    author_email="your.email@example.com",
    description="Extract text, images, and tables from PDF files with analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pdfcoordex",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pdfplumber>=0.10.3",
        "PyMuPDF>=1.23.8",
        "Pillow>=10.0.0",
    ],
    keywords="pdf extraction text images tables analysis",
)