import fitz  # PyMuPDF
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

def render_page_to_image(page, dpi=200):
    zoom = dpi / 72  # 72 is default dpi
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_bytes = pix.tobytes("ppm")
    return Image.open(BytesIO(img_bytes))

def process_file(file_path, dpi=200, max_workers=4):
    doc = fitz.open(file_path)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        images = list(executor.map(lambda page: render_page_to_image(page, dpi), doc))
    return images

# Example usage
if __name__ == "__main__":
    pdf_path = r"testing-pdf\full-book.pdf"
    images = process_file(pdf_path, dpi=200, max_workers=4)
    # Create output directory if it doesn't exist
    import os
    output_dir = "folder/output_images"
    os.makedirs(output_dir, exist_ok=True)

    # Save each image with page number
    for idx, img in enumerate(images):
        output_path = os.path.join(output_dir, f"page_{idx+1}.png")
        img.save(output_path)
        print(f"Saved page {idx+1} to {output_path}")
