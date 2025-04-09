'''Uses Surya Model to layout each page of the pdf . The surya model returns the list of dictonaries of label, bbox, position . '''

from PIL import Image
from surya.layout import LayoutPredictor
from preprocessing import preprocessed_pages
import matplotlib.pyplot as plt
from matplotlib import patches
import cv2


#load model
layout_predictor = LayoutPredictor()

#get boundary boxes
def extract_layout_info(layout_predictions):
    layout_info = []
    for i in layout_predictions:
        for box in i.bboxes:
            info = {
                'label': box.label,
                'position': box.position,
                'bbox': box.bbox
            }
            layout_info.append(info)
    return layout_info

all_pages_layout = []


for page in preprocessed_pages:
        image = Image.fromarray(page)  #converted to PIL format
        layout_predictions = layout_predictor([image])   #main function
        information = extract_layout_info(layout_predictions)
        all_pages_layout.append(information)

bboxes_all = []
def extract_bbox(all_pages_layout):
    bboxes_by_page = []
    for page in all_pages_layout:
        page_bboxes = []
        for element in page:
            x1, y1, x2, y2 = element['bbox']
            label = element['label']
            position = element['position']  # Capture reading order
            
            # Create a dictionary with all needed information
            page_bboxes.append({
                'bbox': (x1, y1, x2, y2),
                'label': label,
                'position': position,
                'section_image': None  # Will store the cropped image section later
            })
        
        # Sort by position to maintain reading order
        page_bboxes.sort(key=lambda x: x['position'])
        bboxes_by_page.append(page_bboxes)
    
    # Now crop the images based on bboxes
    for page_idx, (page_info, page_image) in enumerate(zip(bboxes_by_page, preprocessed_pages)):
        for section in page_info:
            x1, y1, x2, y2 = section['bbox']
            # Convert coordinates to integers for cropping
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            # Crop the section from the page
            section_image = page_image[y1:y2, x1:x2]
            # Store the cropped image in the dictionary
            section['section_image'] = section_image
    
    return bboxes_by_page

def process_page_layout(page_image, layout_predictions):
    """
    Process a single page's layout, crop sections, and maintain reading order.
    
    Args:
        page_image: The original page image (numpy array)
        layout_predictions: Output from layout_predictor
        
    Returns:
        List of dictionaries containing cropped sections and metadata
    """
    # Get layout information
    layout_info = extract_layout_info(layout_predictions)
    
    # Sort by position to maintain reading order
    layout_info.sort(key=lambda x: x['position'])
    
    # Process each section
    sections = []
    for element in layout_info:
        x1, y1, x2, y2 = element['bbox']
        label = element['label']
        position = element['position']
        
        # Convert coordinates to integers for cropping
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        # Crop the section
        section_image = page_image[y1:y2, x1:x2]
        
        # Store section information
        section_data = {
            'label': label,
            'position': position,
            'bbox': (x1, y1, x2, y2),
            'section_image': section_image
        }
        sections.append(section_data)
    
    return sections

def process_single_page(page_image):
    """
    Process a single page through the layout model and return its sections.
    """
    # Convert to PIL format
    pil_image = Image.fromarray(page_image)
    
    # Get layout predictions
    layout_predictions = layout_predictor([pil_image])
    
    # Process the page
    sections = process_page_layout(page_image, layout_predictions)
    
    return sections

def process_text_section(section_image):
    """
    Process a text section.
    Add your text processing logic here.
    """
    # Add your text processing logic
    return processed_text

def process_table_section(section_image):
    """
    Process a table section.
    Add your table processing logic here.
    """
    # Add your table processing logic
    return processed_table

def process_figure_section(section_image):
    """
    Process a figure section.
    Add your figure processing logic here.
    """
    # Add your figure processing logic
    return processed_figure

def process_all_pages(pages):
    """
    Process all pages in the document.
    
    Args:
        pages: List of page images
        
    Returns:
        List of processed sections for all pages
    """
    all_sections = []
    
    for page_idx, page in enumerate(pages):
        # Get sections for this page
        sections = process_single_page(page)
        
        # Process each section based on its type
        for section in sections:
            label = section['label']
            section_image = section['section_image']
            
            if label == 'Text':
                processed_result = process_text_section(section_image)
            elif label == 'Table':
                processed_result = process_table_section(section_image)
            elif label == 'Figure':
                processed_result = process_figure_section(section_image)
            else:
                processed_result = None
            
            # Add processing result to section data
            section['processed_result'] = processed_result
        
        all_sections.append(sections)
    
    return all_sections

# Example usage:
# all_processed_sections = process_all_pages(preprocessed_pages)

# # 2. Load the image
# image_path = r"Z:\TO DO\codes\IIT\ashu\model_output\original dataset\two column and table.png"
# image = Image.open(image_path)
# layout_predictions = layout_predictor([image])  #mainunction
# information = extract_layout_info(layout_predictions)
# print(information)

# # 3. Draw bounding boxes
# for block in information:
#     x1, y1, x2, y2 = list(map(int, block['bbox']))
#     label = block['label']
#     print(label)
#     # Color mapping per label
#     # color_map = {
#     #     'SectionHeader': (255, 0, 0),
#     #     'Text': (0, 255, 0),
#     #     'ListItem': (0, 0, 255),
#     # }
#     # color = color_map.get(label, (255, 255, 0))  # default yellow

#     # # Draw rectangle and label
#     # cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)
#     # cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

# # # 4. Show the image with layout blocks
# # plt.figure(figsize=(12, 12))
# # plt.imshow(image)
# # plt.axis("off")
# # plt.title("Layout Model Output Visualization")
# # plt.show()

# # # Extract bounding boxes and labels
# # all_bboxes = []
# # all_labels = []
# # for element in information:
# #     all_bboxes.append(element['bbox'])
# #     all_labels.append(element['label'])

# # # Display function
# # def display_images_with_bboxes(images, bboxes_list, labels_list):
# #     for i, (image, bboxes, labels) in enumerate(zip(images, bboxes_list, labels_list)):
# #         fig, ax = plt.subplots(figsize=(12, 10))
# #         ax.imshow(image, cmap="gray")
# #         for bbox, label in zip(bboxes, labels):
# #             x1, y1, x2, y2 = bbox
# #             rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='red', facecolor='none')
# #             ax.add_patch(rect)
# #             ax.text(x1, y1-5, label, color='red', fontsize=8)
# #         plt.axis("off")
# #         plt.show()

# # display_images_with_bboxes([image], [all_bboxes], [all_labels])
