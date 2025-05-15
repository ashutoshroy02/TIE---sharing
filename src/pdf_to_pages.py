'''RETURNS A LIST OF PAGES OF PDF <FUNCTION PROCESS_FILE> .Converts the pdf to images and passes it to layout model .it stores the pages as a list and does not save on device (can be saved on device) .
 It handles any input pdf or images any kind . Also the DPI (Density per Inch) is set to 200 for better ocr task and the bbox is calculated according to the dpi (dpi ∝ bbox coordinates) . 
 we can reduce it to faster the process but affect OCR quality'''


'''   Also the DPI (Density per Inch) is set to 200 for better ocr task and the bbox is calculated according to the dpi '''

'''  (DPI ∝ bbox coordinates)   '''

import fitz  # PyMuPDF
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import os

def render_page_to_image(page, dpi=200):
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_bytes = pix.tobytes("ppm")
    return Image.open(BytesIO(img_bytes))

def process_file(file_path, output_folder="output_pages", dpi=200, max_workers=4, save_images=True):
    """
    Converts PDF pages to images and optionally saves them.

    Args:
        file_path (str): Path to PDF file.
        output_folder (str): Folder to save images if enabled.
        dpi (int): DPI for image quality.
        max_workers (int): Number of threads for processing.
        save_images (bool): Enable or disable saving images.

    Returns:
        list: List of PIL Image objects.
    """
    if save_images:
        os.makedirs(output_folder, exist_ok=True)
    
    doc = fitz.open(file_path)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        images = list(executor.map(lambda page: render_page_to_image(page, dpi), doc))
    
    if save_images:
        for i, img in enumerate(images):
            output_path = os.path.join(output_folder, f"page_{i+1}.png")
            img.save(output_path)
            print(f"Saved page {i+1} to {output_path}")
    
    print(f"Processed {len(images)} pages{' and saved them' if save_images else ''}.")
    return images

if __name__ == "__main__":
    pdf_path = r"testing-pdf\book2 (2).pdf"
    output_folder = "output_pages"
    images = process_file(pdf_path, output_folder=output_folder, dpi=150, max_workers=4, save_images=True)
    print(f"Total {len(images)} pages processed.")
    # print(images)
