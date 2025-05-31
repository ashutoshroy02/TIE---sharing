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
from pdf_to_pages import process_file   #returns a list of PIl images (per page) object for the pdf 
from models import recognition_predictor, detection_predictor, layout_predictor
from preprocessing import preprocess_image
import datetime
import sys
import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
# from img2table.ocr.surya import SuryaOCR
# from img2table.document import Image as Docimage


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

def ocr_text_correction(text):
    corrected_ocr_text = ''
    
    #apply logic or llm model
    
    corrected_ocr_text = text
    return corrected_ocr_text

def process_single_page(page_image, page_number=None, padding = 5):
    """
    Process a single page through the layout model and OCR.

    Args:
        page_image: The page image to process
        page_number: The page number (optional)
    """
    try:
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
            # text = ocr_text_correction()
            
            
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

def find_caption(region,image):
    from process_layout import run_processing
    run_processing(image)
    
  

def crop_and_save_images(image, regions, output_folder, padding=5):
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
    page_number = regions[0].get('position') if regions else None

    # Dictionary to store metadata for this page
    page_metadata = {
        'page_number': page_number+1,
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
            'captions' : region.get('captions', '')

        }

        # Generate description for images and tables
        if label.lower() in ['image', 'table', 'picture', 'figure']:
            # Get all regions above (with lower position), sorted by position (top to bottom)
            prev_regions = [r for r in regions if r['position'] < position]
            prev_regions_sorted = sorted(prev_regions, key=lambda r: r['position'])
            # Concatenate their OCR text in order
            description_texts = [r.get('ocr_text', '') for r in prev_regions_sorted]
            description = " ".join(description_texts)
            region_metadata['description'] = description
        else:
            region_metadata['description'] = ""


        if label.lower() == 'table':
            # Save cropped table images
            table_image_path = os.path.join('cropped_tables', f"table_page{page_number}_region{idx+1}.png")
            cv2.imwrite(os.path.join(output_folder_tables, f"table_page{page_number}_region{idx+1}.png"), cropped_image)
            region_metadata['saved_path'] = table_image_path
            print(f"Saved table image: {table_image_path}")
            
        elif label.lower() in ['figure', 'image', 'picture']:
            # Save cropped figure images
            figure_image_path = os.path.join('cropped_figures', f"figure_page{page_number}_region{idx+1}.png")
            cv2.imwrite(os.path.join(output_folder_figures, f"figure_page{page_number}_region{idx+1}.png"), cropped_image)
            region_metadata['saved_path'] = figure_image_path
            print(f"Saved figure image: {figure_image_path}")

        page_metadata['regions'].append(region_metadata)

    return page_metadata

def process_pdf(pdf_path, output_folder, padding=7):
    """
    Process a PDF file and crop its regions with integrated OCR.
    
    Args:
        pdf_path: Path to the PDF file
        output_folder: Directory to save cropped images and metadata
        padding: Padding to add around cropped regions
        
    """
    # Convert PDF to PIL images
    try:
        pdf_images = process_file(pdf_path, output_folder)    #pdf_iamges is list of PIL image   [<PIL.PpmImagePlugin.PpmImageFile image mode=RGB size=3444x4880 at 0x7FF14736B800>, <PIL.PpmImagePlugin.PpmImageFile image mode=RGB size=3444x4880 at 0x7FF114802B40> ]
        print(f"Extracted {len(pdf_images)} pages from PDF: {pdf_path}")
        
        if not pdf_images:
            print("No images extracted from PDF")
            return
        
        # Intialize the List to store metadata for all pages of the pdf
        all_pages_metadata = []
        
        # Process each page
        for page_num, page_image in enumerate(pdf_images, start=1):
            print(f"\nProcessing page {page_num}")
            
            # Process page (layout + OCR)
            regions = process_single_page(page_image, page_num, padding = 5)
            #format for regions ocr       [{'label': 'Picture', 'position': 0, 'bbox': (141.2578125, 259.641357421875, 3322.921875, 1130.37890625), 'page_number': 1, 'ocr_text': 'INTRODUCTION AND H 90.69 A SUMMARY OF THE RESULTS $ B.B. LAL'}, {'label': 'Text', 'position': 1, 'bbox': (361.97314453125, 1207.28759765625, 3124.48828125, 2053.283203125), 'page_number': 1, 'ocr_text': "A lthough in the earlier report on the recent environmental change has come <b>Thexequations at Kalibangan we had up because of the canal that has been</b> given a detailed account of the location laid out in the dry bed of the Ghaggar of the site and its environment, it may (Sarasvati). Likewise, one can well imagine not be out of place here to recall some of that during the Harappan times when the mighty Sarasvati itself was flowing past it, since we don't expect the readers to remember all that; and perhaps some of the site the environment must have been no less green. Indeed, the discovery of a them may not have even seen the earlier ploughed field with criss-cross furrow report.<sup>1</sup> marks, ascribable to the Early Harappan times,<sup>2</sup> fully endorses such a view. Located on the left bank of the now-"}, {'label': 'Text', 'position': 3, 'bbox': (355.6669921875, 1981.740234375, 1697.6162109375, 3299.91943359375), 'page_number': 1, 'ocr_text': "Located on the left bank of the now- dry Ghaggar (ancient Sarasvati) river in Hanumangarh District of Rajasthan, Kalibangan (Lat. 29<sup>0</sup> 29' N; Long. 74<sup>°</sup> 08' E) is one of the most important sites excavated on the Indian side of the border after Independence. As would be seen a little later, it has made some very valuable contributions to our knowledge of the Harappan Civilization (also known as the Indus/Indus-Sarasvatî Civilization). The site is about 6 km south of the nearest railway station, called Pilibangan, which lies between Hanumangarh and Suratgarh. From Delhi, it is a little over 300 km by road in a north-westerly direction (cf. Fig. 1.1)."}, {'label': 'Text', 'position': 5, 'bbox': (1750.587890625, 2131.38427734375, 3095.900390625, 2429.47998046875), 'page_number': 1, 'ocr_text': 'The ancient site consists of three mounds (Fig. 4.1). Of these, the one in the middle (called KLB-2) is the largest, though it has been badly eroded on the'}, {'label': 'Text', 'position': 7, 'bbox': (351.462890625, 3393.521484375, 1705.18359375, 4071.538818359375), 'page_number': 1, 'ocr_text': 'As one moves in this area, one sees during the winter season luscious fields of wheat interspersed with those of mustard, the latter welcoming the visitor by waving their lovely yellow flowers. But all this is a recent development. In the 1950s when we were exploring the area we were greeted by nothing but sand, often swirling up in the air and blinding us. The'}, {'label': 'Text', 'position': 8, 'bbox': (1735.453125, 2450.048583984375, 3100.9453125, 4055.79150390625), 'page_number': 1, 'ocr_text': 'southern side. It measures approximately 240m east-west and seems to have been not less than 360m north-south. That on the west (called KLB-1) measures roughly 240m north-south and 120m east-west. As would have been observed, the longer axis in both the cases is north-south, i.e. almost at right angles to the adjacent river, which is somewhat unusual, since normally habitations stretch along the river. Anyway, both the mounds rise to a height of approximately 10m above the surrounding plains. The third mound, named KLB-3, is a bit away to the east of KLB-2 and is very much smaller in area, approximately 70m x 50m, and only 2.5m in height. The reason for this small size of the last-named mound lies in the fact that it was not a residential complex but was used only for a limited (ritualistic) purpose.'}, {'label': 'ListItem', 'position': 11, 'bbox': (352.3037109375, 4204.35107421875, 3080.765625, 4322.01025390625), 'page_number': 1, 'ocr_text': 'B.B. Lal, J.P. Joshi et al. 2003, Excavations at Kalibangan: The Early Harappans, New Delhi: Archaeological Survey of India.'}, {'label': 'ListItem', 'position': 12, 'bbox': (351.252685546875, 4324.9814453125, 849.228515625, 4386.7822265625), 'page_number': 1, 'ocr_text': '<i>Ibid.</i>, pp. 95-98.'}]
            # print(regions)
            
            #add caption in region
            # regions = find_caption(regions, page_image:PIL format)
            
            if not regions:
                print(f"No regions detected on page {page_num}")
                continue

            # Crop and save images based on regions and get metadata
            page_metadata = crop_and_save_images(page_image, regions, output_folder, padding)
            all_pages_metadata.append(page_metadata)
        

        # Create and save complete PDF metadata
        complete_metadata = {
            'pdf_path': pdf_path,
            'total_pages': len(all_pages_metadata),
            'total_regions': sum(page['total_regions'] for page in all_pages_metadata),
            'pages': all_pages_metadata
        }
        
        
        # Save complete PDF metadata
        complete_metadata_path = os.path.join(
            output_folder, 'metadata', f'{os.path.basename(output_folder)}_pdf_metadata.json'
        )
        with open(complete_metadata_path, 'w') as f:
            json.dump(complete_metadata, f, indent=4)
        print(f"Saved complete PDF metadata to: {complete_metadata_path}")
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    #pdf_folder = "../testing-documents"
    #pdf_folder = "/mnt/storage/nivedita/pdf_corpus_2"
    pdf_folder = "/home/nivedita/night_test"    
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('1.png')]
    print(f"Number of PDF files in '{pdf_folder}': {len(pdf_files)}")
    for idx, pdf_file in enumerate(pdf_files, start=1):
        #code for pdf file
        pdf_path = os.path.join(pdf_folder, pdf_file)
        pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
        output_folder = os.path.join("Result", pdf_basename)
        #main process
        print(f"Processing PDF: {pdf_path}")
        process_pdf(pdf_path, output_folder, )
