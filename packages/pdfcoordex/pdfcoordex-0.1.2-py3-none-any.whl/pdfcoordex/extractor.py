import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
import io

class PDFCoordExtractor:
    def __init__(self, pdf_path):
        """Initialize PDF extractor with a PDF file path"""
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.page_count = len(self.doc)
    
    def extract_page(self, page_number):
        """Extract all elements from a single page
        
        Args:
            page_number (int): Page number (1-indexed)
            
        Returns:
            dict: Dictionary containing text, images, and tables
        """
        if page_number < 1 or page_number > self.page_count:
            raise ValueError(f"Page {page_number} is out of range (1-{self.page_count})")
        
        page_data = {
            'page_number': page_number,
            'text': '',
            'images': [],
            'tables': []
        }
        
        # Extract all text as single string
        page = self.doc[page_number - 1]
        page_data['text'] = page.get_text()
        
        # Extract and analyze images
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = self.doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Open image with PIL
                pil_image = Image.open(io.BytesIO(image_bytes))
                
                # Basic image analysis
                width, height = pil_image.size
                mode = pil_image.mode
                format_type = base_image.get("ext", "unknown")
                
                # Image description (basic analysis)
                aspect_ratio = width / height if height > 0 else 0
                
                if aspect_ratio > 1.5:
                    orientation = "wide/landscape"
                elif aspect_ratio < 0.67:
                    orientation = "tall/portrait"
                else:
                    orientation = "square/balanced"
                
                description = f"Image {img_index + 1}: {format_type.upper()} format, {width}x{height} pixels, {orientation} orientation"
                
                # Try to determine image type based on characteristics
                if width > 400 and height > 400:
                    img_type = "Large diagram or figure"
                elif width < 100 or height < 100:
                    img_type = "Icon or small graphic"
                else:
                    img_type = "Medium-sized image or chart"
                
                analysis = f"{img_type}. Color mode: {mode}. Likely contains visual information relevant to the document content."
                
                page_data['images'].append({
                    'description': description,
                    'analysis': analysis
                })
            except Exception as e:
                page_data['images'].append({
                    'description': f"Image {img_index + 1}: Could not analyze",
                    'analysis': f"Error: {str(e)}"
                })
        
        # Extract tables
        with pdfplumber.open(self.pdf_path) as pdf:
            plumber_page = pdf.pages[page_number - 1]
            tables = plumber_page.find_tables()
            
            for table in tables:
                extracted_table = table.extract()
                if extracted_table:
                    page_data['tables'].append(extracted_table)
        
        return page_data
    
    def extract_all_pages(self):
        """Extract all pages from the PDF
        
        Returns:
            dict: Dictionary with page data for all pages
        """
        results = {}
        for page_num in range(1, self.page_count + 1):
            results[f'page{page_num}'] = self.extract_page(page_num)
        return results
    
    def save_to_text_file(self, output_file='extracted_content.txt'):
        """Save extracted content to a plain text file
        
        Args:
            output_file (str): Output filename (default: extracted_content.txt)
            
        Returns:
            str: Path to the output file
        """
        all_pages = self.extract_all_pages()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("PDF CONTENT EXTRACTION\n")
            f.write(f"File: {self.pdf_path}\n")
            f.write(f"Total Pages: {self.page_count}\n")
            f.write("="*80 + "\n\n")
            
            for page_name, page_data in all_pages.items():
                f.write("\n" + "="*80 + "\n")
                f.write(f"PAGE {page_data['page_number']}\n")
                f.write("="*80 + "\n\n")
                
                # Write text content
                f.write("--- TEXT CONTENT ---\n")
                f.write(page_data['text'])
                f.write("\n\n")
                
                # Write image analysis
                if page_data['images']:
                    f.write("--- IMAGES ---\n")
                    for idx, img in enumerate(page_data['images'], 1):
                        f.write(f"\nImage {idx}:\n")
                        f.write(f"  Description: {img['description']}\n")
                        f.write(f"  Analysis: {img['analysis']}\n")
                    f.write("\n")
                else:
                    f.write("--- IMAGES ---\n")
                    f.write("No images found on this page.\n\n")
                
                # Write tables
                if page_data['tables']:
                    f.write("--- TABLES ---\n")
                    for idx, table in enumerate(page_data['tables'], 1):
                        f.write(f"\nTable {idx}:\n")
                        for row in table:
                            # Format row as text
                            row_text = " | ".join([str(cell) if cell else "" for cell in row])
                            f.write(f"  {row_text}\n")
                        f.write("\n")
                else:
                    f.write("--- TABLES ---\n")
                    f.write("No tables found on this page.\n\n")
        
        return output_file
    
    def close(self):
        """Close the PDF document"""
        self.doc.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()