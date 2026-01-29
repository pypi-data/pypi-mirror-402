from setuptools import setup, find_packages

setup(
    name="pdfcoordex",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pdfplumber>=0.10.3",
        "PyMuPDF>=1.23.8",
        "camelot-py>=0.11.0",
        "opencv-python>=4.8.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
    ],
    python_requires=">=3.8",
)
