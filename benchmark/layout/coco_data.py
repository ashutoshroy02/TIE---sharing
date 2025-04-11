from PIL import Image
from surya.layout import LayoutPredictor
from pdf_to_pages import process_file
import matplotlib.pyplot as plt
from matplotlib import patches
import cv2
import numpy as np
import json
import os
from datetime import datetime
from tqdm import tqdm
import glob

# Load model
layout_predictor = LayoutPredictor()

def convert_to_coco_format(layout_predictions, image_id, image_path, image_size):
    """
    Convert Surya layout predictions to COCO format.
    
    Args:
        layout_predictions: Output from layout_predictor
        image_id: Unique ID for the image
        image_path: Path to the image file
        image_size: Tuple of (width, height)
        
    Returns:
        Dictionary in COCO format
    """
    # COCO categories mapping
    category_map = {
        'Text': 1,
        'Table': 2,
        'Figure': 3,
        'ListItem': 4,
        'SectionHeader': 5,
        'PageHeader': 6,
        'PageFooter': 7,
        'TextInlineMath': 8,
        'Caption': 9,
        'TableOfContents': 10,
        'Footnote': 11,
        'Picture': 12,
        'Handwriting': 13,  # Added Handwriting category
        'Equation': 14,     # Added Equation category
        'Unknown': 15       # Added Unknown category for fallback
    }
    
    # Initialize COCO format
    coco_data = {
        "info": {
            "description": "Document Layout Dataset",
            "url": "",
            "version": "1.0",
            "year": datetime.now().year,
            "contributor": "",
            "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "licenses": [],
        "images": [{
            "id": image_id,
            "file_name": os.path.basename(image_path),
            "width": image_size[0],
            "height": image_size[1],
            "date_captured": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }],
        "annotations": [],
        "categories": [
            {"id": 1, "name": "Text", "supercategory": "text"},
            {"id": 2, "name": "Table", "supercategory": "table"},
            {"id": 3, "name": "Figure", "supercategory": "figure"},
            {"id": 4, "name": "ListItem", "supercategory": "text"},
            {"id": 5, "name": "SectionHeader", "supercategory": "text"},
            {"id": 6, "name": "PageHeader", "supercategory": "text"},
            {"id": 7, "name": "PageFooter", "supercategory": "text"},
            {"id": 8, "name": "TextInlineMath", "supercategory": "text"},
            {"id": 9, "name": "Caption", "supercategory": "text"},
            {"id": 10, "name": "TableOfContents", "supercategory": "text"},
            {"id": 11, "name": "Footnote", "supercategory": "text"},
            {"id": 12, "name": "Picture", "supercategory": "figure"},
            {"id": 13, "name": "Handwriting", "supercategory": "text"},
            {"id": 14, "name": "Equation", "supercategory": "text"},
            {"id": 15, "name": "Unknown", "supercategory": "text"}
        ]
    }
    
    # Add annotations
    annotation_id = 1
    for prediction in layout_predictions:
        for box in prediction.bboxes:
            x1, y1, x2, y2 = box.bbox
            width = x2 - x1
            height = y2 - y1
            
            # Handle unknown labels
            try:
                category_id = category_map[box.label]
            except KeyError:
                print(f"Warning: Unknown label '{box.label}' found in image {image_path}. Mapping to 'Unknown' category.")
                category_id = category_map['Unknown']
            
            annotation = {
                "id": annotation_id,
                "image_id": image_id,
                "category_id": category_id,
                "bbox": [x1, y1, width, height],
                "area": width * height,
                "segmentation": box.polygon,
                "iscrowd": 0,
                "confidence": float(box.confidence),
                "position": box.position,
                "original_label": box.label  # Store original label for reference
            }
            
            coco_data["annotations"].append(annotation)
            annotation_id += 1
    
    return coco_data

def process_image_to_coco(image_path, image_id):
    """
    Process an image and return its annotations in COCO format.
    
    Args:
        image_path: Path to the image file
        image_id: Unique ID for the image
        
    Returns:
        Dictionary containing image info and annotations
    """
    # Process the image
    pages = process_file(image_path)
    if not pages:
        print(f"No pages found in {image_path}")
        return None
    
    # Get image size
    image = pages[0]
    if isinstance(image, Image.Image):
        width, height = image.size
    else:
        height, width = image.shape[:2]
    
    # Get layout predictions
    if isinstance(image, Image.Image):
        pil_image = image
    else:
        pil_image = Image.fromarray(image)
    
    layout_predictions = layout_predictor([pil_image])
    
    # Convert to COCO format
    coco_data = convert_to_coco_format(
        layout_predictions,
        image_id=image_id,
        image_path=image_path,
        image_size=(width, height)
    )
    
    return coco_data

def process_folder_to_coco(folder_path, output_path):
    """
    Process all images in a folder and save their annotations in COCO format.
    
    Args:
        folder_path: Path to the folder containing images
        output_path: Path to save the COCO annotations
    """
    # Get all image files
    image_extensions = ['*.png', '*.jpg', '*.jpeg']
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(folder_path, ext)))
    
    if not image_files:
        print(f"No images found in {folder_path}")
        return
    
    # Initialize combined COCO data
    combined_coco = {
        "info": {
            "description": "Document Layout Dataset",
            "url": "",
            "version": "1.0",
            "year": datetime.now().year,
            "contributor": "",
            "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "licenses": [],
        "images": [],
        "annotations": [],
        "categories": [
            {"id": 1, "name": "Text", "supercategory": "text"},
            {"id": 2, "name": "Table", "supercategory": "table"},
            {"id": 3, "name": "Figure", "supercategory": "figure"},
            {"id": 4, "name": "ListItem", "supercategory": "text"},
            {"id": 5, "name": "SectionHeader", "supercategory": "text"},
            {"id": 6, "name": "PageHeader", "supercategory": "text"},
            {"id": 7, "name": "PageFooter", "supercategory": "text"},
            {"id": 8, "name": "TextInlineMath", "supercategory": "text"},
            {"id": 9, "name": "Caption", "supercategory": "text"},
            {"id": 10, "name": "TableOfContents", "supercategory": "text"},
            {"id": 11, "name": "Footnote", "supercategory": "text"},
            {"id": 12, "name": "Picture", "supercategory": "figure"},
            {"id": 13, "name": "Handwriting", "supercategory": "text"},
            {"id": 14, "name": "Equation", "supercategory": "text"},
            {"id": 15, "name": "Unknown", "supercategory": "text"}
        ]
    }
    
    # Process each image
    annotation_id = 1
    for image_id, image_path in enumerate(tqdm(image_files, desc="Processing images")):
        coco_data = process_image_to_coco(image_path, image_id + 1)
        if coco_data:
            # Add image info
            combined_coco["images"].extend(coco_data["images"])
            
            # Add annotations with updated IDs
            for ann in coco_data["annotations"]:
                ann["id"] = annotation_id
                annotation_id += 1
            combined_coco["annotations"].extend(coco_data["annotations"])
    
    # Save to file
    with open(output_path, 'w') as f:
        json.dump(combined_coco, f, indent=2)
    
    print(f"COCO annotations saved to {output_path}")
    print(f"Processed {len(image_files)} images")
    print(f"Total annotations: {len(combined_coco['annotations'])}")

# Example usage
if __name__ == "__main__":
    # Input folder path
    folder_path = r'Z:\TO DO\codes\IIT\ashu\model_output\original dataset'
    
    # Output COCO annotations path
    output_path = 'coco_annotations.json'
    
    # Process all images in the folder and save COCO annotations
    process_folder_to_coco(folder_path, output_path)