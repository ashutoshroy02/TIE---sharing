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
# from pdf_to_pages import process_file
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor
# from preprocessing import preprocess_image

# Initialize Surya models globally
recognition_predictor = RecognitionPredictor()
detection_predictor = DetectionPredictor()

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
        
        # Convert region to PIL Image for Surya OCR
        region_pil = Image.fromarray(region_image)
        
        # Get OCR predictions for the region
        region_predictions = recognition_predictor([region_pil], [None], detection_predictor)
        print(region_predictions)
       # Extract text from predictions
        text = ""
        # Accessing the 'text_lines' attribute of 'OCRResult'
        if region_predictions and region_predictions[0].text_lines:
            text = " ".join([line.text.strip() for line in region_predictions[0].text_lines])

        
        # Store the result
        results[region_id] = {
            'type': region_type,
            'bbox': bbox,
            'position': region.get('position', i),  # Maintain reading order
            'content': text
        }
    
    return results

def process_image_with_layout(image_path: Union[str, Image.Image], layout_file: str = None) -> Dict[str, Any]:
    """
    Process a single image using layout detection and OCR.

    Args:
        image_path: Path to the image file OR a PIL Image object
        layout_file: Optional path to a JSON file with layout information

    Returns:
        Dictionary containing OCR results
    """
    from layout_model import  process_single_page

    # Check if image_path is a string path or already a PIL image
    if isinstance(image_path, str):
        images = process_file(image_path)
        if not images:
            return {"error": "No images found in the file"}
        image = images[0]
    else:
        image = image_path  # Already a PIL Image

    # Get layout info
    if layout_file and os.path.exists(layout_file):
        with open(layout_file, 'r') as f:
            regions = json.load(f)
    else:
        from layout_model import process_single_page
        regions = process_single_page(image)

    results = process_regions(image, regions)
    return results


if __name__ == "__main__":
    # Example usage
    file_path = r"/content/fullbook.pdf"
    image_list = process_file(file_path)
    print(image_list)
    # Process all images using the same function
    all_results = {}
    for i, image in enumerate(image_list):
        result = process_image_with_layout(image)
        all_results[f"page_{i+1}"] = result

    # # Output all results as JSON
    # print(json.dumps(all_results, indent=2, ensure_ascii=False))
    with open("all_results.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
