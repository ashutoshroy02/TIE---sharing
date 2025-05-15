'''
STEP 2 : Uses Surya Model to layout each page of the pdf . The surya model returns the list of dictonaries of label, bbox, position .
This file return the json for the layout of the page only label, bbox, position and section image . 
'''

'''   Also the DPI (Density per Inch) is set to 200 for better ocr task and the bbox is calculated according to the dpi '''

'''  (DPI ∝ bbox coordinates)   '''

from PIL import Image
from surya.layout import LayoutPredictor
from pdf_to_pages import process_file
import matplotlib.pyplot as plt
from matplotlib import patches
import json
import numpy as np

#load model
layout_predictor = LayoutPredictor()

#------------------------------------------#
# #process pdf to pages
# import fitz  # PyMuPDF
# from PIL import Image
# from concurrent.futures import ThreadPoolExecutor
# from io import BytesIO

# def render_page_to_image(page, dpi=200):
#     zoom = dpi / 72  # 72 is default dpi
#     mat = fitz.Matrix(zoom, zoom)
#     pix = page.get_pixmap(matrix=mat, alpha=False)
#     img_bytes = pix.tobytes("ppm")
#     return Image.open(BytesIO(img_bytes))

# def process_file(file_path, dpi=200, max_workers=4):
#     doc = fitz.open(file_path)
#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         images = list(executor.map(lambda page: render_page_to_image(page, dpi), doc))
#     return images

#####
#------------------------------------------#
def extract_layout_info(layout_predictions):
    """
    Extract layout information from Surya model predictions.
    Returns list of dictionaries containing label, position, and bbox for each element.
    """
    layout_info = []
    for prediction in layout_predictions:
        for box in prediction.bboxes:
            info = {
                'label': box.label,
                'position': box.position,
                'bbox': box.bbox
            }
            layout_info.append(info)
    return layout_info

def process_page_layout(page_image, layout_predictions):
    """
    Process a single page's layout and identify regions of interest without cropping.
    
    Args:
        page_image: The original page image (numpy array)
        layout_predictions: Output from layout_predictor
        
    Returns:
        List of dictionaries containing region information and metadata
    """
    # Get layout information
    layout_info = extract_layout_info(layout_predictions)
    
    # Sort by position to maintain reading order
    layout_info.sort(key=lambda x: x['position'])
    
    # Process each section
    regions = []
    for element in layout_info:
        x1, y1, x2, y2 = element['bbox']
        label = element['label']
        position = element['position']
        
        # Store region information
        region_data = {
            'label': label,
            'position': position,
            'bbox': (x1, y1, x2, y2),
            'region_type': label  # Use the label as the region type for OCR processing
        }
        regions.append(region_data)
    
    return regions


def process_single_page(page_image):
    """
    Process a single page through the layout model and return its regions.
    """
    # Check if page_image is already a PIL Image
    if not isinstance(page_image, Image.Image):
        # Convert to PIL format if it's a numpy array
        pil_image = Image.fromarray(page_image)
    else:
        pil_image = page_image
    
    # Get layout predictions
    layout_predictions = layout_predictor([pil_image])
    
    # Convert PIL image to numpy array for processing
    if isinstance(page_image, Image.Image):
        page_image = np.array(page_image)
    
    # Process the page
    return process_page_layout(page_image, layout_predictions)


def serialize_sections(sections):
    """
    Convert sections to a JSON-serializable format.
    
    Args:
        sections (list): List of dictionaries containing section information
        
    Returns:
        str: JSON string representation of the sections
    """
    return json.dumps(sections, indent=2)


def visualize_regions(image, regions):
    """
    Visualize the regions on the original image.
    
    Args:
        image: The original image (PIL Image or numpy array)
        regions: List of region dictionaries with bbox information
    """
    # Create a figure to display the original image with bounding boxes
    plt.figure(figsize=(15, 10))
    plt.imshow(image)
    
    # Add bounding boxes for each region
    for region in regions:
        bbox = region['bbox']
        x, y, w, h = bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        # Create rectangle patch
        rect = patches.Rectangle(
            (x, y), w, h,
            linewidth=2,
            edgecolor='r',
            facecolor='none',
            label=region['label']
        )
        plt.gca().add_patch(rect)
        
        # Add label text
        plt.text(x, y-5, region['label'], color='red', fontsize=12, 
                bbox=dict(facecolor='white', alpha=0.7))
    
    plt.title('Document Layout with Regions')
    plt.axis('off')
    plt.show()


def process_region_for_ocr(image, region):
    """
    Process a specific region for OCR based on its type.
    
    Args:
        image: The original image (numpy array)
        region: Dictionary containing region information
        
    Returns:
        Processed OCR result based on region type
    """
    # Extract region coordinates
    x1, y1, x2, y2 = region['bbox']
    
    # Convert to integers only for extracting the region
    x1_int, y1_int, x2_int, y2_int = int(x1), int(y1), int(x2), int(y2)
    
    # Extract the region from the original image
    region_image = image[y1_int:y2_int, x1_int:x2_int]
    
    # Process based on region type
    region_type = region['label'].lower()
    
    if 'text' in region_type or 'paragraph' in region_type:
        # Process as text
        # Here you would call your text OCR function
        return f"Text OCR result for region: {region['label']}"
    
    elif 'table' in region_type:
        # Process as table
        # Here you would call your table OCR function
        return f"Table OCR result for region: {region['label']}"
    
    elif 'map' in region_type or 'figure' in region_type or 'image' in region_type:
        # Process as map/figure
        # Here you would call your map/figure processing function
        return f"Map/Figure processing result for region: {region['label']}"
    
    else:
        # Default processing
        return f"Default OCR result for region: {region['label']}"


# if __name__ == "__main__":
#     pdf_images = process_file(r"model_output\original dataset\two column and table.png")
#     if pdf_images:
#         # Process the first page
#         regions = process_single_page(pdf_images[0])
        
#         # Serialize regions to JSON
#         regions_json = serialize_sections(regions)
#         print("\nRegions in JSON format:")
#         print(regions_json)
        
#         # Visualize regions on the original image
#         visualize_regions(pdf_images[0], regions)
        
#         # Process each region for OCR
#         print("\nProcessing regions for OCR:")
#         for region in regions:
#             result = process_region_for_ocr(np.array(pdf_images[0]), region)
#             print(f"Region: {region['label']} - {result}")

