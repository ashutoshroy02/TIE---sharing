'''
OCR Processor: Processes different types of content (text, tables, maps) using Surya OCR.
This file works with the output from layout_model.py, which provides regions with bounding boxes.
'''

import sys
import os
import numpy as np
from PIL import Image
import cv2
import json
import io
from typing import Dict, List, Any, Tuple, Union
from pdf_to_pages import process_file    #returns a list of PIl images (per page) object for the pdf 
from preprocessing import preprocess_image
from caption import process_page_for_captions
from text_correct import generate_description
import torch
import re

# Model loader functions (safe for multiprocessing)
def get_layout_predictor():
    from surya.layout import LayoutPredictor
    return LayoutPredictor()

def get_recognition_predictor():
    from surya.recognition import RecognitionPredictor
    return RecognitionPredictor()

def get_detection_predictor():
    from surya.detection import DetectionPredictor
    return DetectionPredictor()


def extract_layout_info(layout_predictions):
    """
    Input args Format :

    Extract layout information from Surya model predictions.
    Returns list of dictionaries containing label, position, and bbox for each element.
    Return Format :

    """
    layout_info = []    #creates an empty list to store the information.
    for prediction in layout_predictions:   #layout predictions has python syntax
        for box in prediction.bboxes:
            info = {
                'label': box.label,
                'position': box.position,
                'bbox': box.bbox,
                # 'label_confidence': box.top_k[0][1]
            }
            layout_info.append(info)
    return layout_info   


def process_page_layout(page_image, layout_predictions):   #convert python syntax to json
    """
    Process a single page's layout and identify regions of interest.
    
    Args:
        page_image: The original page image (numpy array)
        layout_predictions: Output from layout_predictor
        
    Returns:
        return json of metadata
    """
    # Get layout information
    layout_info = extract_layout_info(layout_predictions)
     #output format      [{'label': 'Picture', 'position': 0, 'bbox': [141.2578125, 259.641357421875, 3322.921875, 1130.37890625]}, {'label': 'Text', 'position': 1, 'bbox': [361.97314453125, 1207.28759765625, 3124.48828125, 2053.283203125]}, {'label': 'Text', 'position': 3, 'bbox': [355.6669921875, 1981.740234375, 1697.6162109375, 3299.91943359375]}, {'label': 'Text', 'position': 5, 'bbox': [1750.587890625, 2131.38427734375, 3095.900390625, 2429.47998046875]}, {'label': 'Text', 'position': 7, 'bbox': [351.462890625, 3393.521484375, 1705.18359375, 4071.538818359375]}, {'label': 'Text', 'position': 8, 'bbox': [1735.453125, 2450.048583984375, 3100.9453125, 4055.79150390625]}, {'label': 'ListItem', 'position': 11, 'bbox': [352.3037109375, 4204.35107421875, 3080.765625, 4322.01025390625]}, {'label': 'ListItem', 'position': 12, 'bbox': [351.252685546875, 4324.9814453125, 849.228515625, 4386.7822265625]}]
    
    # Sort by position to maintain reading order
    layout_info.sort(key=lambda x: x['position'])
    
    try:
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
                # 'region_type': label
            }
            regions.append(region_data)
        return regions
    except Exception as e:
        print(f"Error in process_page_layout: {e}")
        return []


def process_single_page(page_image, page_number=None, padding = 5):
    """
    Process a single page through the layout model and OCR.

    Args:
        page_image: The page image to process
        page_number: The page number (optional)
    """
    try:
        # Load models inside the function (per process)
        layout_predictor = get_layout_predictor()
        recognition_predictor = get_recognition_predictor()
        detection_predictor = get_detection_predictor()

        # Check if page_image is already a PIL Image
        if not isinstance(page_image, Image.Image):
            # Convert to PIL format if it's a numpy array
            pil_image = Image.fromarray(page_image)
        else:
            pil_image = page_image        #PIL image 

        # Get layout predictions
        layout_predictions = layout_predictor([pil_image])      #applying surya layout model  
        # model output   [LayoutResult(bboxes=[LayoutBox(polygon=[[1503.38671875, 329.69384765625], [3043.76953125, 329.69384765625], [3043.76953125, 407.19873046875], [1503.38671875, 407.19873046875]], confidence=0.72802734375, label='SectionHeader', position=0, top_k={'SectionHeader': 0.72802734375, 'Text': 0.26904296875, 'Picture': 0.0024166107177734375, 'Figure': 0.0002455711364746094, 'PageHeader': 0.0001208186149597168}, bbox=[1503.38671875, 329.69384765625, 3043.76953125, 407.19873046875]), LayoutBox(polygon=[[318.6708984375, 544.024658203125], [3047.1328125, 544.024658203125], [3047.1328125, 704.6982421875], [318.6708984375, 704.6982421875]], confidence=0.99951171875, label='Text', position=1, top_k={'Text': 0.99951171875, 'SectionHeader': 0.00045108795166015625, 'ListItem': 2.5033950805664062e-06, 'Picture': 1.6689300537109375e-06, 'Caption': 1.3113021850585938e-06}, bbox=[318.6708984375, 544.024658203125, 3047.1328125, 704.6982421875]), LayoutBox(polygon=[[638.1826171875, 717.814453125], [2704.078125, 717.814453125], [2704.078125, 785.7802734375], [638.1826171875, 785.7802734375]], confidence=1.0, label='SectionHeader', position=2, top_k={'SectionHeader': 1.0, 'Text': 3.314018249511719e-05, 'Caption': 7.510185241699219e-06, 'Table': 6.198883056640625e-06, 'Picture': 1.9669532775878906e-06}, bbox=[638.1826171875, 717.814453125, 2704.078125, 785.7802734375]), LayoutBox(polygon=[[287.560546875, 875.208984375], [3052.177734375, 875.208984375], [3052.177734375, 4331.51806640625], [287.560546875, 4331.51806640625]], confidence=1.0, label='Table', position=3, top_k={'Table': 1.0, 'SectionHeader': 1.728534698486328e-05, 'Text': 1.0251998901367188e-05, 'TableOfContents': 8.344650268554688e-06, 'Picture': 9.5367431640625e-07}, bbox=[287.560546875, 875.208984375, 3052.177734375, 4331.51806640625]), LayoutBox(polygon=[[1619.419921875, 4443.8291015625], [1711.91015625, 4443.8291015625], [1711.91015625, 4498.4990234375], [1619.419921875, 4498.4990234375]], confidence=0.92724609375, label='Text', position=5, top_k={'Text': 0.92724609375, 'Picture': 0.0292510986328125, 'TextInlineMath': 0.0245208740234375, 'SectionHeader': 0.0081024169921875, 'PageFooter': 0.007472991943359375}, bbox=[1619.419921875, 4443.8291015625, 1711.91015625, 4498.4990234375])], image_bbox=[0.0, 0.0, 3444.0, 4880.0], sliced=True)]
        #layout prediction has python syntax
    
        # Convert PIL image to numpy array for processing
        if isinstance(page_image, Image.Image):
            page_image = np.array(page_image)           #numpy image 

        # Process the page layout
        regions = process_page_layout(page_image, layout_predictions)  #image in numpy goes as input  #output in json(metadata) from layout predictions(python syntax)

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
            # Add padding to the bounding box
            x1_padded = max(0, int(x1) - padding)
            y1_padded = max(0, int(y1) - padding)
            x2_padded = min(page_image.shape[1], int(x2) + padding)
            y2_padded = min(page_image.shape[0], int(y2) + padding)
            
            region_image = page_image[y1_padded:y2_padded, x1_padded:x2_padded]
            
            #save the croped regions
            # cv2.imwrite(f"haha/{region_id}{region_type}.png",region_image )

            # Preprocess the region image  (numpy array)
            preprocessed_region = preprocess_image(region_image)
            
            # Convert preprocessed region to PIL Image for Surya OCR
            region_pil = Image.fromarray(preprocessed_region)    #PIL image

            # if region_type == 'table':
            #     # Use Surya OCR only for table regions
            #     ocr = SuryaOCR(langs=["en"])
            #     # Convert PIL image to BytesIO
            #     img_bytes = io.BytesIO()
            #     region_pil.save(img_bytes, format='PNG')
            #     img_bytes.seek(0)  # Reset pointer to start
            #     img = Docimage(src=img_bytes)
            #     tables = img.extract_tables(ocr=ocr, borderless_tables=False)

            #     ocr_json = tables[0].df.to_json(orient='index')
            #     print(ocr_json)

            
            # else:
            # Get OCR predictions for the region (other than table)
            region_predictions = recognition_predictor([region_pil], ['ocr_with_boxes'], detection_predictor)
            #output format              [OCRResult(text_lines=[TextLine(polygon=[[84.0, 11.0], [508.0, 12.0], [506.0, 65.0], [81.0, 64.0]], confidence=0.9416306865842718, text='<i>Ibid.</i>, pp. 95-98.', chars=[TextChar(polygon=[[81.0, 11.0], [81.0, 12.0], [82.0, 12.0], [82.0, 11.0]], confidence=0.5527318716049194, text='<i>', bbox_valid=False, bbox=[81.0, 11.0, 82.0, 12.0]), TextChar(polygon=[[92.0, 11.0], [109.0, 11.0], [109.0, 63.0], [92.0, 63.0]], confidence=0.9192655682563782, text='I', bbox_valid=True, bbox=[92.0, 11.0, 109.0, 63.0]), TextChar(polygon=[[107.0, 11.0], [137.0, 11.0], [137.0, 63.0], [107.0, 63.0]], confidence=0.9895163178443909, text='b', bbox_valid=True, bbox=[107.0, 11.0, 137.0, 63.0]), TextChar(polygon=[[134.0, 11.0], [148.0, 11.0], [148.0, 63.0], [134.0, 63.0]], confidence=0.9897438883781433, text='i', bbox_valid=True, bbox=[134.0, 11.0, 148.0, 63.0]), TextChar(polygon=[[148.0, 11.0], [183.0, 11.0], [183.0, 63.0], [148.0, 63.0]], confidence=0.9897485375404358, text='d', bbox_valid=True, bbox=[148.0, 11.0, 183.0, 63.0]), TextChar(polygon=[[180.0, 11.0], [200.0, 11.0], [200.0, 63.0], [180.0, 63.0]], confidence=0.9701963663101196, text='.', bbox_valid=True, bbox=[180.0, 11.0, 200.0, 63.0]), TextChar(polygon=[[81.0, 11.0], [81.0, 12.0], [82.0, 12.0], [82.0, 11.0]], confidence=0.6571718454360962, text='</i>', bbox_valid=False, bbox=[81.0, 11.0, 82.0, 12.0]), TextChar(polygon=[[194.0, 11.0], [214.0, 11.0], [214.0, 63.0], [194.0, 63.0]], confidence=0.9874247908592224, text=',', bbox_valid=True, bbox=[194.0, 11.0, 214.0, 63.0]), TextChar(polygon=[[207.0, 11.0], [226.0, 11.0], [226.0, 63.0], [207.0, 63.0]], confidence=0.9924522042274475, text=' ', bbox_valid=True, bbox=[207.0, 11.0, 226.0, 63.0]), TextChar(polygon=[[224.0, 11.0], [258.0, 11.0], [258.0, 63.0], [224.0, 63.0]], confidence=0.9477123022079468, text='p', bbox_valid=True, bbox=[224.0, 11.0, 258.0, 63.0]), TextChar(polygon=[[259.0, 11.0], [292.0, 11.0], [292.0, 63.0], [259.0, 63.0]], confidence=0.9894282221794128, text='p', bbox_valid=True, bbox=[259.0, 11.0, 292.0, 63.0]), TextChar(polygon=[[291.0, 11.0], [307.0, 11.0], [307.0, 63.0], [291.0, 63.0]], confidence=0.9904721975326538, text='.', bbox_valid=True, bbox=[291.0, 11.0, 307.0, 63.0]), TextChar(polygon=[[303.0, 11.0], [331.0, 11.0], [331.0, 63.0], [303.0, 63.0]], confidence=0.9914366602897644, text=' ', bbox_valid=True, bbox=[303.0, 11.0, 331.0, 63.0]), TextChar(polygon=[[324.0, 11.0], [360.0, 11.0], [360.0, 63.0], [324.0, 63.0]], confidence=0.9733585119247437, text='9', bbox_valid=True, bbox=[324.0, 11.0, 360.0, 63.0]), TextChar(polygon=[[360.0, 11.0], [392.0, 11.0], [392.0, 63.0], [360.0, 63.0]], confidence=0.993025541305542, text='5', bbox_valid=True, bbox=[360.0, 11.0, 392.0, 63.0]), TextChar(polygon=[[388.0, 11.0], [410.0, 11.0], [410.0, 63.0], [388.0, 63.0]], confidence=0.9871915578842163, text='-', bbox_valid=True, bbox=[388.0, 11.0, 410.0, 63.0]), TextChar(polygon=[[409.0, 11.0], [442.0, 11.0], [442.0, 63.0], [409.0, 63.0]], confidence=0.9885165691375732, text='9', bbox_valid=True, bbox=[409.0, 11.0, 442.0, 63.0]), TextChar(polygon=[[440.0, 11.0], [472.0, 11.0], [472.0, 63.0], [440.0, 63.0]], confidence=0.991243839263916, text='8', bbox_valid=True, bbox=[440.0, 11.0, 472.0, 63.0]), TextChar(polygon=[[470.0, 11.0], [485.0, 11.0], [485.0, 63.0], [470.0, 63.0]], confidence=0.9903462529182434, text='.', bbox_valid=True, bbox=[470.0, 11.0, 485.0, 63.0])], original_text_good=False, words=[], bbox=[81.0, 11.0, 508.0, 65.0])], image_bbox=[0.0, 0.0, 508.0, 72.0])]
    
            # Extract all texts for a particular regions 
            text = ""
            if region_predictions and region_predictions[0].text_lines:
                text = " ".join([line.text.strip() for line in region_predictions[0].text_lines])
            # print(text)
            
            #ocr correction via llm
            # try:
            #     text = ocr_text_correction(text)  # from text_correct.py
            # except Exception as e:
            #     print(f"OCR correction failed: {e}")
            #     # Optionally, keep the original text or set to empty
            
            
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
    except Exception as e:
        print(f"Error processing page {page_number}: {e}")
        return []
 
  
def crop_and_save_images(image, regions, output_folder, padding=5, page_url=None):
    """
    Crop and save images based on detected regions.

    Args:
        image: PIL Image of the page  [<PIL.PpmImagePlugin.PpmImageFile image mode=RGB size=3444x4880 at 0x7FF14736B800>]
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
        'page_url': page_url,
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
            'ocr_text': region.get('ocr_text', '') ,
            'captions' : region.get('captions', ''),
            'description': region.get('description', '')

        }



        if label.lower() == 'table':
            # Save cropped table images
            table_image_path = os.path.join('cropped_tables', f"table_page{page_number}_region{idx+1}.png")
            cv2.imwrite(os.path.join(output_folder_tables, f"table_page{page_number}_region{idx+1}.png"), cropped_image)
            region_metadata['saved_path'] = table_image_path
            # print(f"Saved table image: {table_image_path}")
            
        elif label.lower() in ['figure', 'image', 'picture']:
            # Save cropped figure images
            figure_image_path = os.path.join('cropped_figures', f"figure_page{page_number}_region{idx+1}.png")
            cv2.imwrite(os.path.join(output_folder_figures, f"figure_page{page_number}_region{idx+1}.png"), cropped_image)
            region_metadata['saved_path'] = figure_image_path
            # print(f"Saved figure image: {figure_image_path}")

        page_metadata['regions'].append(region_metadata)

    # print(page_metadata)
    return page_metadata


def process_pdf(pdf_path, output_folder, padding=7):
    try:
        pdf_pages_and_urls = process_file(pdf_path, output_folder)
        print(f"Extracted {len(pdf_pages_and_urls)} pages from PDF: {pdf_path}")
        
        if not pdf_pages_and_urls:
            print("No pages extracted from PDF")
            return
        
        all_pages_metadata = []
        for page_num, (page_image, page_url) in enumerate(pdf_pages_and_urls, start=1):
            print(f"\nProcessing page {page_num}")
            regions = process_single_page(page_image, page_num, padding=5)
            if not regions:
                print(f"No regions detected on page {page_num}")
                continue
            page_metadata = crop_and_save_images(page_image, regions, output_folder, padding, page_url=page_url)
            page_metadata = process_page_for_captions(page_metadata, page_num)
            all_pages_metadata.append(page_metadata)

            # Release models and free GPU memory after each batch (page)
            
            torch.cuda.empty_cache()
            del regions, page_metadata, page_image
        
        for id, page_metadata in enumerate(all_pages_metadata, start=1):
            prev_page_metadata = all_pages_metadata[id - 2] if id > 1 else None
            next_page_metadata = all_pages_metadata[id] if id < len(all_pages_metadata) else None
            for region in page_metadata['regions']:
                caption = region.get('captions', None)
                if caption is not None:
                    match = re.search(r'(?i)\b([A-Za-z]|Fig|Figure|Table|Image|Img)\.?\s*\d+(\.\d+)*', caption)
                    if match:
                        cropped_caption = caption[:match.end()]
                        generate_description(prev_page_metadata, page_metadata, next_page_metadata, cropped_caption)
            

        complete_metadata = {
            'pdf_path': pdf_path,
            'total_pages': len(all_pages_metadata),
            'total_regions': sum(page['total_regions'] for page in all_pages_metadata),
            'pages': all_pages_metadata
        }
        complete_metadata_path = os.path.join(
            output_folder, 'metadata', f'{os.path.basename(output_folder)}_pdf_metadata.json'
        )
        with open(complete_metadata_path, 'w') as f:
            json.dump(complete_metadata, f, indent=4)
        print(f"Saved complete PDF metadata to: {complete_metadata_path}")
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")

if __name__ == "__main__":
    pass
