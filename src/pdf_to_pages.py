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


def process_file(file_path, output_folder, process_dpi=200, save_dpi=75, max_workers=4, save_images=True):
    """
    Converts PDF pages to images and optionally saves them.
    Uses process_dpi for the returned PIL images and save_dpi for saved images.

    Args:
        file_path (str): Path to PDF file.
        output_folder (str): Folder to save images if enabled.
        process_dpi (int): DPI for the returned PIL Image objects.
        save_dpi (int): DPI for saving images (resizes from process_dpi).
        max_workers (int): Number of threads for processing.
        save_images (bool): Enable or disable saving images.

    Returns:
        list: List of (PIL Image, page_url) tuples.
    """

    if save_images:
        os.makedirs(output_folder, exist_ok=True)

    doc = fitz.open(file_path)
    # Render images at process_dpi
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        images = list(executor.map(lambda page: render_page_to_image(page, process_dpi), doc))

    page_urls = []
    if save_images:
        # Resize and save images at save_dpi
        scale_factor = save_dpi / process_dpi
        for i, img in enumerate(images):
            output_path = os.path.join(output_folder, f"page_{i+1}.png")
            # Resize the image to save_dpi before saving
            new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
            resized_img = img.resize(new_size, Image.Resampling.LANCZOS) # Using LANCZOS filter for quality
            resized_img.save(output_path)
            page_urls.append(output_path)
    else:
        # If not saving, you can still provide a logical name or None
        page_urls = [None] * len(images)

    # Return list of (image, page_url) tuples
    return list(zip(images, page_urls))

