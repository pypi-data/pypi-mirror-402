import pdfplumber
import fitz  # PyMuPDF

def process_page(pdf_path, page_number):
    output = {
        f"page{page_number + 1}": {
            "text_blocks": [],
            "images": [],
            "tables": []
        }
    }

    # -------- TEXT & TABLES --------
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]

        for word in page.extract_words(use_text_flow=True):
            output[f"page{page_number + 1}"]["text_blocks"].append({
                "text": word["text"],
                "x0": word["x0"],
                "y0": word["top"],
                "x1": word["x1"],
                "y1": word["bottom"]
            })

        tables = page.extract_tables()
        for table in tables:
            output[f"page{page_number + 1}"]["tables"].append({
                "data": table,
                "bbox": page.bbox
            })

    # -------- IMAGES --------
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)

    for img in page.get_images(full=True):
        bbox = page.get_image_bbox(img)
        output[f"page{page_number + 1}"]["images"].append({
            "x0": bbox.x0,
            "y0": bbox.y0,
            "x1": bbox.x1,
            "y1": bbox.y1,
            "width": bbox.width,
            "height": bbox.height
        })

    return output
