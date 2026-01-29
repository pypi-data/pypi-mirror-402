import multiprocessing
import pdfplumber
from .page_processor import process_page

def extract_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

    with multiprocessing.Pool() as pool:
        results = pool.starmap(
            process_page,
            [(pdf_path, i) for i in range(total_pages)]
        )

    final_output = {}
    for page in results:
        final_output.update(page)

    return final_output
