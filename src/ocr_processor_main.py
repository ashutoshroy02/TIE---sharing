'''
OCR Processor: Processes different types of content (text, tables, maps) using Surya OCR.
This file works with the output from layout_model.py, which provides regions with bounding boxes.
'''

import numpy as np
from PIL import Image
import cv2
import json
import os
from typing import Dict, List, Any, Tuple, Union
from pdf_to_pages import process_file   #returns a list of PIl images (per page) object for the pdf 
from models import recognition_predictor, detection_predictor, layout_predictor
from preprocessing import preprocess_image
import datetime


def extract_layout_info(layout_predictions):
    """
    Input args Format :

    Extract layout information from Surya model predictions.
    Returns list of dictionaries containing label, position, and bbox for each element.
    Return Format :

    """
    layout_info = []    #creates an empty list to store the information.
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
    Process a single page's layout and identify regions of interest.
    
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
            'region_type': label
        }
        regions.append(region_data)
    
    return regions


def process_single_page(page_image, page_number=None):
    """
    Process a single page through the layout model and OCR.

    Args:
        page_image: The page image to process
        page_number: The page number (optional)
    """
    # Check if page_image is already a PIL Image
    if not isinstance(page_image, Image.Image):
        # Convert to PIL format if it's a numpy array
        pil_image = Image.fromarray(page_image)
    else:
        pil_image = page_image        #PIL image
    
    # Get layout predictions
    layout_predictions = layout_predictor([pil_image])      #applying surya layout model  
    
    # Convert PIL image to numpy array for processing
    if isinstance(page_image, Image.Image):
        page_image = np.array(page_image)           #numpy image 
    
    # Process the page layout
    regions = process_page_layout(page_image, layout_predictions)
    
    # Add page number to each region
    for region in regions:
        region['page_number'] = page_number
    
    # Process OCR for all regions at once
    results = {}
    for i, region in enumerate(regions):
        region_id = f"region_{i}"
        region_type = region['label'].lower()
        bbox = region['bbox']
        
        # Extract the region from the original image
        x1, y1, x2, y2 = [int(coord) for coord in bbox]
        region_image = page_image[y1:y2, x1:x2]
        
        # Preprocess the region image  (numpy array)
        preprocessed_region = preprocess_image(region_image)
        
        # Convert preprocessed region to PIL Image for Surya OCR
        region_pil = Image.fromarray(preprocessed_region)
        
        # Get OCR predictions for the region
        region_predictions = recognition_predictor([region_pil], ['ocr_with_boxes'], detection_predictor)
        
        # Extract text from predictions
        text = ""
        if region_predictions and region_predictions[0].text_lines:
            text = " ".join([line.text.strip() for line in region_predictions[0].text_lines])
        
        # Store the result
        results[region_id] = {
            'type': region_type,
            'bbox': bbox,
            'position': region.get('position', i),
            'content': text
        }
        
        # Add OCR text directly to the region
        region['ocr_text'] = text
    
    return regions


def crop_and_save_images(image, regions, output_folder, padding=5):
    """
    Crop and save images based on detected regions.

    Args:
        image: PIL Image of the page
        regions: List of region dictionaries
        output_folder: Directory to save cropped images
        padding: Padding to add around cropped regions
    """
    # Define subfolders for tables, figures, and metadata
    output_folder_tables = os.path.join(output_folder, 'cropped_tables')
    output_folder_figures = os.path.join(output_folder, 'cropped_figures')
    output_folder_metadata = os.path.join(output_folder, 'metadata')

    # Ensure output directories exist
    os.makedirs(output_folder_tables, exist_ok=True)
    os.makedirs(output_folder_figures, exist_ok=True)
    os.makedirs(output_folder_metadata, exist_ok=True)
    
    # Get page number from the first region
    page_number = regions[0].get('page_number') if regions else None
    
    # Dictionary to store metadata for this page
    page_metadata = {
        'page_number': page_number,
        'processed_date': str(datetime.datetime.now()),
        'total_regions': len(regions),
        'regions': []
    }

    # Convert PIL image to numpy array for OpenCV processing
    if isinstance(image, Image.Image):
        image = np.array(image)

    for idx, region in enumerate(regions):
        x1, y1, x2, y2 = region['bbox']
        label = region['label']
        position = region['position']

        # Add padding to the bounding box
        x1_padded = max(0, int(x1) - padding)
        y1_padded = max(0, int(y1) - padding)
        x2_padded = min(image.shape[1], int(x2) + padding)
        y2_padded = min(image.shape[0], int(y2) + padding)

        # Crop the image with padding
        cropped_image = image[y1_padded:y2_padded, x1_padded:x2_padded]

        # Create metadata for this region
        region_metadata = {
            'region_id': idx + 1,
            'label': label,
            'position': position,
            'original_bbox': [x1, y1, x2, y2],
            'padded_bbox': [x1_padded, y1_padded, x2_padded, y2_padded],
            'image_size': cropped_image.shape[:2],
            'ocr_text': region.get('ocr_text', '')  # Include OCR text in metadata
        }

        if label.lower() == 'table':
            # Save cropped table images
            table_image_path = os.path.join('cropped_tables', f"table_page{page_number}_region{idx+1}.png")
            cv2.imwrite(os.path.join(output_folder_tables, f"table_page{page_number}_region{idx+1}.png"), cropped_image)
            region_metadata['saved_path'] = table_image_path
            print(f"Saved table image: {table_image_path}")
        elif label.lower() in ['figure', 'image']:
            # Save cropped figure images
            figure_image_path = os.path.join('cropped_figures', f"figure_page{page_number}_region{idx+1}.png")
            cv2.imwrite(os.path.join(output_folder_figures, f"figure_page{page_number}_region{idx+1}.png"), cropped_image)
            region_metadata['saved_path'] = figure_image_path
            print(f"Saved figure image: {figure_image_path}")

        page_metadata['regions'].append(region_metadata)

    # Save metadata to JSON file in the metadata subfolder
    if page_number is not None:
        metadata_path = os.path.join(output_folder_metadata, f'page_{page_number}_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(page_metadata, f, indent=4)
        print(f"Saved metadata to: {metadata_path}")

def process_pdf(pdf_path, output_folder, padding=5):
    """
    Process a PDF file and crop its regions with integrated OCR.
    
    Args:
        pdf_path: Path to the PDF file
        output_folder: Directory to save cropped images and metadata
        padding: Padding to add around cropped regions
    """
    # Convert PDF to PIL images
    pdf_images = process_file(pdf_path)
    
    if not pdf_images:
        print("No images extracted from PDF")
        return
    
    # Intialize the List to store metadata for all pages of the pdf
    all_pages_metadata = []
    
    # Process each page
    for page_num, page_image in enumerate(pdf_images, start=1):
        print(f"\nProcessing page {page_num}")
        
        # Process page (layout + OCR)
        regions = process_single_page(page_image, page_num)
        if not regions:
            print(f"No regions detected on page {page_num}")
            continue

        # Crop and save images based on regions
        crop_and_save_images(page_image, regions, output_folder, padding)
        
        # Read the page metadata that was just saved
        metadata_path = os.path.join(output_folder, 'metadata', f'page_{page_num}_metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                page_metadata = json.load(f)
                all_pages_metadata.append(page_metadata)
    

    # Create and save complete PDF metadata
    complete_metadata = {
        'pdf_path': pdf_path,
        'total_pages': len(all_pages_metadata),
        'processed_date': str(datetime.datetime.now()),
        'total_regions': sum(page['total_regions'] for page in all_pages_metadata),
        'pages': all_pages_metadata
    }
    
    
    # Save complete PDF metadata
    complete_metadata_path = os.path.join(output_folder, 'metadata', 'complete_pdf_metadata.json')
    with open(complete_metadata_path, 'w') as f:
        json.dump(complete_metadata, f, indent=4)
    print(f"Saved complete PDF metadata to: {complete_metadata_path}")


if __name__ == "__main__":
    # Example usage
    pdf_path = r"../testing-documents/diff-pages-book.pdf"  # Replace with your PDF file path
    output_folder = "output-try"  # Replace with your desired output folder
    process_pdf(pdf_path, output_folder)



























''' if using table detection '''

'''
def process_regions(image: Union[np.ndarray, Image.Image], regions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process all regions in an image using Surya OCR.

    Args:
        image: The original image (numpy array or PIL Image)
        regions: List of region dictionaries with bbox and label information

    Returns:
        Dictionary containing OCR results for each region
    """
    # Convert PIL Image to numpy array if needed
    if isinstance(image, Image.Image):
        image = np.array(image)

    # Preprocess the entire image
    # preprocessed_image = preprocess_image(image)

    # Convert back to PIL Image for Surya OCR
    pil_image = Image.fromarray(image)

    # Get OCR predictions for the entire image
    predictions = recognition_predictor([pil_image], [None], detection_predictor)

    results = {}

    for i, region in enumerate(regions):
        region_id = f"region_{i}"
        region_type = region['label'].lower()
        bbox = region['bbox']
        
        # Extract the region from the original image
        x1, y1, x2, y2 = [int(coord) for coord in bbox]
        region_image = image[y1:y2, x1:x2]
        
        # Convert region to PIL Image
        region_pil = Image.fromarray(region_image)
        
        if 'table' in region_type:
            # Process table using img2table
            # Convert PIL image to BytesIO
            img_bytes = io.BytesIO()
            region_pil.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Create Image object from BytesIO
            table_img = TableImage(src=img_bytes)
            
            # Extract tables
            tables = table_img.extract_tables(ocr=table_ocr, borderless_tables=False)
            
            # Convert table to markdown format
            table_content = ""
            if tables:
                table_content = tables[0].df.to_markdown(index=False)
            
            table_result = {
                'type': 'table',
                'bbox': bbox,
                'position': region.get('position', i),
                'content': table_content
            }
            results[region_id] = table_result
        else:
            # Process non-table regions using Surya OCR
            region_predictions = recognition_predictor([region_pil], [None], detection_predictor)
            
            # Extract text from predictions
            text = ""
            if region_predictions and region_predictions[0].text_lines:
                text = " ".join([line.text.strip() for line in region_predictions[0].text_lines])
            
            # Store the result
            results[region_id] = {
                'type': region_type,
                'bbox': bbox,
                'position': region.get('position', i),
                'content': text
            }
    
    return results
'''
