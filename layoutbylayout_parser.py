# import cv2
# import numpy as np
# import subprocess
# import json
# import os
# import tempfile

# class LayoutAnalyzer:
#     """Analyzes page layout to detect different content regions."""
    
#     def __init__(self, surya_model_path=None):
#         """
#         Initialize layout analyzer with Surya OCR.
        
#         Args:
#             surya_model_path: Path to Surya OCR model. If None, will use default installed model.
#         """
#         self.surya_model_path = surya_model_path
    
#     def analyze(self, image):
#         """
#         Analyze the page layout to identify different content regions.
        
#         Args:
#             image: Input image (numpy array or path to image)
            
#         Returns:
#             List of dictionaries with region information:
#             [
#                 {
#                     "type": "text"|"table"|"image"|"figure",
#                     "bbox": [x1, y1, x2, y2],
#                     "position": (y1, x1)  # For sorting top-to-bottom, left-to-right
#                 },
#                 ...
#             ]
#         """
#         # Save image temporarily if input is numpy array
#         if not isinstance(image, str):
#             with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
#                 temp_path = temp.name
#                 cv2.imwrite(temp_path, image)
#                 image_path = temp.name
#         else:
#             image_path = image
        
#         # Call Surya OCR (or simulation for this example)
#         layout_regions = self._call_surya_ocr(image_path)
        
#         # Clean up temporary file if created
#         if not isinstance(image, str):
#             os.unlink(temp_path)
        
#         return layout_regions
    
#     def _call_surya_ocr(self, image_path):
#         """
#         Call Surya OCR to detect layout regions.
        
#         Note: This is a simplified version. In an actual implementation,
#         you would use the Surya OCR API or CLI tools.
#         """
#         # Placeholder for actual Surya OCR call
#         # In a real implementation, you would do something like:
#         # result = subprocess.run(
#         #     ["surya", "layout", "--input", image_path, "--output", "json"],
#         #     capture_output=True, text=True, check=True
#         # )
#         # layout_data = json.loads(result.stdout)
        
#         # For demonstration purposes, we'll create a simulated layout analysis
#         # by using basic OpenCV operations to detect possible text regions
        
#         # Read the image
#         image = cv2.imread(image_path)
       
        
#         # Find contours in the image
#         contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
#         # Filter contours and classify them
#         regions = []
#         for i, contour in enumerate(contours):
#             x, y, w, h = cv2.boundingRect(contour)
            
#             # Filter out very small regions
#             if w < 50 or h < 20:
#                 continue
                
#             # Calculate area
#             area = w * h
#             aspect_ratio = w / float(h)
            
#             # Classify region based on simple heuristics
#             # This is very simplified - Surya would use a ML model
#             if aspect_ratio > 3 and h < 100:
#                 region_type = "text"
#             elif aspect_ratio < 1.5 and aspect_ratio > 0.7:
#                 region_type = "image"
#             elif aspect_ratio > 1.5 and h > 100:
#                 region_type = "table"
#             else:
#                 region_type = "text"
            
#             regions.append({
#                 "type": region_type,
#                 "bbox": [x, y, x+w, y+h],
#                 "position": (y, x)  # For sorting top-to-bottom, left-to-right
#             })
        
#         return regions


# import os
# from PIL import Image, ImageDraw
# from surya.detection import DetectionPredictor
# import numpy as np

# # Initialize the detector
# det_predictor = DetectionPredictor()

# # Input and output directories
# input_dir = "input_directory"  
# output_dir = "output_directory"  # Replace with your output directory path

# # Create output directory if it doesn't exist
# os.makedirs(output_dir, exist_ok=True)

# # Process all jpg files in the directory
# for filename in os.listdir(input_dir):
#     if filename.lower().endswith('.jpg'):
#         # Construct full file paths
#         input_path = os.path.join(input_dir, filename)
#         output_path = os.path.join(output_dir, filename)
        
#         # Open image and get predictions
#         image = Image.open(input_path)
#         predictions = det_predictor([image])
        
#         # Draw bounding boxes around detected regions
#         draw = ImageDraw.Draw(image)
        
#         # Process predictions for the image
#         for pred in predictions[0].bboxes:
#             # Extract bounding box coordinates
#             bbox = pred.bbox
#             x1, y1, x2, y2 = bbox
            
#             # Get confidence score
#             confidence = pred.confidence
            
#             # For now, all regions are treated as text
#             # In a real implementation, you would classify by type
#             region_type = "text"
#             color = {
#                 "text": (0, 255, 0),    # Green for text
#                 "table": (0, 0, 255),   # Blue for tables
#                 "image": (255, 0, 0)    # Red for images
#             }.get(region_type, (128, 128, 128))
            
#             # Draw rectangle
#             draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            
#             # Add label with confidence score
#             label = f"{region_type} ({confidence:.2f})"
#             draw.text((x1, y1-15), label, fill=color)
        
#         # Save the processed image with the same name
#         image.save(output_path)
#         print(f"Processed and saved: {filename}")



import layoutparser as lp
import cv2
import os
from pathlib import Path

# Initialize the layout model
model = lp.Detectron2LayoutModel(
    config_path='lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config',
    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8]
)

def analyze_layout(image_path, output_dir):
    # Read the image
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Detect the layout
    layout = model.detect(image)
    
    # Draw the layout
    viz_image = lp.draw_box(image, layout, box_width=3)
    
    # Save the visualized result
    output_path = os.path.join(output_dir, f"analyzed_{os.path.basename(image_path)}")
    cv2.imwrite(output_path, cv2.cvtColor(viz_image, cv2.COLOR_RGB2BGR))
    
    # Print the layout analysis
    print(f"\nAnalysis for {os.path.basename(image_path)}:")
    for block in layout:
        print(f"Found {block.type} with confidence {block.score:.2f}")

def process_directory(input_dir, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process all images in the directory
    image_extensions = ['.jpg', '.jpeg', '.png']
    for file in os.listdir(input_dir):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            input_path = os.path.join(input_dir, file)
            try:
                analyze_layout(input_path, output_dir)
                print(f"Successfully processed {file}")
            except Exception as e:
                print(f"Error processing {file}: {str(e)}")

# Set your input and output directories
input_dir = r"Z:\TO DO\codes\IIT\ashu\model_output\original dataset"
output_dir = r"Z:\TO DO\codes\IIT\ashu\model_output\layout_layoutparser"

# Run the analysis
process_directory(input_dir, output_dir)