'''
STEP 2 : Uses Surya Model to layout each page of the pdf . The surya model returns the list of dictonaries of label, bbox, position .
This file return the json for the layout of the page only label, bbox, position and section image . 
'''

from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from matplotlib import patches
import json
import numpy as np
import os
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import logging
from datetime import datetime
from pathlib import Path
import pytesseract  # For OCR
import re
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from surya.layout import LayoutPredictor
    layout_predictor = LayoutPredictor()
    logger.info("Surya model loaded successfully")
except ImportError:
    logger.error("Surya model not found. Please install it using: pip install surya")
    layout_predictor = None

class LayoutProcessor:
    def __init__(self):
        # Get the directory where the script is located
        self.script_dir = Path(__file__).parent.absolute()
        
        # Set up output directories in the script's directory
        self.base_output_dir = self.script_dir / 'output_regions'
        self.metadata_file = self.base_output_dir / 'layout_metadata.json'
        self.region_counter = self.load_region_counter()
        self.setup_output_directories()
        
        # Initialize statistics structure
        self.statistics = {
            'total_regions': 0,
            'regions_by_type': {},
            'captions_by_type': {}
        }
        
        # Define caption patterns with comprehensive table detection
        self.caption_patterns = {
            'figure': [
                r'^(?:Fig\.|Figure\.|Fig;|Figure;)\s*\d+[.:]?\s*',
                r'^(?:Figure|Fig)\s*\d+[.:]?\s*',
                r'^(?:Figure|Fig)\s*\d+\s*[A-Z]?[.:]?\s*'  # For figures with letters (e.g., Fig 1A)
            ],
            'table': [
                r'^(?:Table\.|Table;)\s*\d+[.:]?\s*',
                r'^(?:Table)\s*\d+[.:]?\s*',
                r'^(?:Tbl\.|Tbl;)\s*\d+[.:]?\s*',
                r'^(?:Table)\s*\d+\s*[A-Z]?[.:]?\s*',  # For tables with letters (e.g., Table 1A)
                r'^(?:Table)\s*\d+\s*\([A-Z]\)[.:]?\s*',  # For tables with parenthetical letters (e.g., Table 1(A))
                r'^(?:Table)\s*\d+\s*-\s*\d+[.:]?\s*',  # For table ranges (e.g., Table 1-2)
                r'^(?:Table)\s*\d+\s*and\s*\d+[.:]?\s*',  # For multiple tables (e.g., Table 1 and 2)
                r'^(?:Table)\s*\d+\s*to\s*\d+[.:]?\s*'  # For table ranges with 'to' (e.g., Table 1 to 2)
            ],
            'map': [
                r'^(?:Map\.|Map;)\s*\d+[.:]?\s*',
                r'^(?:Map)\s*\d+[.:]?\s*'
            ]
        }
        
        # Compile regex patterns for each type
        self.caption_regex = {
            'figure': re.compile('|'.join(self.caption_patterns['figure']), re.IGNORECASE),
            'table': re.compile('|'.join(self.caption_patterns['table']), re.IGNORECASE),
            'map': re.compile('|'.join(self.caption_patterns['map']), re.IGNORECASE)
        }
        
        # Define valid region types for caption association
        self.valid_region_types = {
            'figure': ['figure', 'image', 'picture'],
            'table': ['table'],
            'map': ['map']
        }

    def setup_output_directories(self):
        """Create output directories if they don't exist."""
        self.label_dirs = {
            'maps': self.base_output_dir / 'maps',
            'tables': self.base_output_dir / 'tables',
            'text': self.base_output_dir / 'text',
            'images': self.base_output_dir / 'images',
            'figures': self.base_output_dir / 'figures',
            'captions': self.base_output_dir / 'captions',
            'metadata': self.base_output_dir / 'metadata',  # Directory for individual metadata files
            'json_output': self.base_output_dir / 'json_output'  # New directory for JSON outputs
        }
        
        for dir_path in self.label_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def load_region_counter(self):
        """Load the current region counter from metadata file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                # Load region counter and potentially existing statistics
                # Initialize statistics if not present
                self.statistics = metadata.get('statistics', {
                    'total_regions': 0,
                    'regions_by_type': {},
                    'captions_by_type': {}
                })
                # Ensure nested dictionaries exist
                self.statistics['regions_by_type'] = self.statistics.get('regions_by_type', {})
                self.statistics['captions_by_type'] = self.statistics.get('captions_by_type', {})

                return metadata.get('region_counter', 0)
            except Exception as e:
                logger.error(f"Error loading metadata: {str(e)}")
        # Initialize statistics if file does not exist or loading fails
        self.statistics = {
            'total_regions': 0,
            'regions_by_type': {},
            'captions_by_type': {}
        }
        return 0
    
    def save_region_metadata(self, region):
        """Save individual metadata file for each region."""
        metadata_path = self.label_dirs['metadata'] / f"region_{region['number']}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(region, f, indent=4)
        return metadata_path

    def validate_caption(self, text, region_type=None):
        """Validate caption text and format."""
        if not text or not isinstance(text, str):
            return False
            
        text = text.strip()
        
        # Check minimum length (e.g., "Table 1" is minimum)
        if len(text) < 6:
            return False
            
        # Check if text matches any caption pattern
        if not self.is_caption(text, region_type):
            return False
            
        # Additional validation for table captions
        if region_type == 'table' or (region_type is None and self.get_caption_type(text) == 'table'):
            # Check for common table caption issues
            if text.count('.') > 2:  # Too many periods
                return False
            if text.count(';') > 1:  # Too many semicolons
                return False
            if not re.search(r'\d', text):  # Must contain a number
                return False
                
        return True

    def save_type_metadata(self, regions):
        """Save metadata files by region type with enhanced structure."""
        # Group regions by type
        type_groups = {
            'text': [],
            'table': [],
            'image': []  # Will include figures and pictures
        }
        
        # Process and validate regions
        for region in regions:
            label = region['label'].lower()
            
            # Validate caption if present
            if 'caption' in region:
                if not self.validate_caption(region['caption'], self.get_caption_type(region['caption'])):
                    logger.warning(f"Invalid caption format for region {region['number']}: {region['caption']}")
                    region['caption_valid'] = False
                else:
                    region['caption_valid'] = True
            
            # Categorize region
            if label == 'table':
                type_groups['table'].append(region)
            elif label in ['figure', 'image', 'picture']:
                type_groups['image'].append(region)
            elif label == 'text':
                type_groups['text'].append(region)
        
        # Save metadata for each type with enhanced structure
        for region_type, regions in type_groups.items():
            if regions:  # Only save if there are regions of this type
                metadata = {
                    'type': region_type,
                    'count': len(regions),
                    'regions': regions,
                    'statistics': {
                        'total_regions': len(regions),
                        'regions_with_captions': sum(1 for r in regions if 'caption' in r),
                        'valid_captions': sum(1 for r in regions if r.get('caption_valid', False)),
                        'invalid_captions': sum(1 for r in regions if 'caption' in r and not r.get('caption_valid', True))
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                metadata_path = self.label_dirs['metadata'] / f"{region_type}_metadata.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4)
                logger.info(f"Saved {region_type} metadata to {metadata_path}")

    def save_metadata(self, new_metadata):
        """Save metadata to JSON file with enhanced structure."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    existing_metadata = json.load(f)
            except Exception:
                existing_metadata = {
                    'regions': [],
                    'region_counter': 0,
                    'statistics': {
                        'total_regions': 0,
                        'regions_by_type': {},
                        'captions_by_type': {}
                    }
                }
        else:
            existing_metadata = {
                'regions': [],
                'region_counter': 0,
                'statistics': {
                    'total_regions': 0,
                    'regions_by_type': {},
                    'captions_by_type': {}
                }
            }
        
        # Update region counter
        existing_metadata['region_counter'] = self.region_counter
        
        # Process new regions
        for region in new_metadata['regions']:
            label = region['label'].lower()
            region_type = 'image' if label in ['figure', 'image', 'picture'] else label
            
            # Create region summary with enhanced information
            region_summary = {
                'number': region['number'],
                'type': region_type,
                'position': region['position'],
                'bbox': region['bbox'],
                'has_caption': 'caption' in region,
                'caption_type': region.get('caption_type', None),
                'caption_valid': region.get('caption_valid', True) if 'caption' in region else None,
                'timestamp': datetime.now().isoformat()
            }
            existing_metadata['regions'].append(region_summary)
            
            # Update statistics
            existing_metadata['statistics']['total_regions'] += 1
            existing_metadata['statistics']['regions_by_type'][region_type] = \
                existing_metadata['statistics']['regions_by_type'].get(region_type, 0) + 1
            
            if 'caption' in region:
                caption_type = region.get('caption_type', 'unknown')
                existing_metadata['statistics']['captions_by_type'][caption_type] = \
                    existing_metadata['statistics']['captions_by_type'].get(caption_type, 0) + 1
        
        # Save updated metadata
        with open(self.metadata_file, 'w') as f:
            json.dump(existing_metadata, f, indent=4)

    def draw_region_labels(self, image, regions):
        """Draw region numbers, labels, and captions on the image."""
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("arial.ttf", 96)
        except:
            font = ImageFont.load_default()
        
        for region in regions:
            x1, y1, x2, y2 = map(int, region['bbox'])
            
            # Prepare label text
            label = f"{region['number']}: {region['label']}"
            if 'caption' in region:
                label += f"\nCaption: {region['caption']}"
            
            # Draw region rectangle
            draw.rectangle([x1, y1, x2, y2], outline='#FF0000', width=16)
            
            # Calculate text size for background
            text_bbox = draw.textbbox((x1, y1-120), label, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Draw background for text
            draw.rectangle(
                [x1, y1-120, x1 + text_width + 40, y1-120 + text_height + 40],
                fill='#FFFFFF',
                outline='#000000',
                width=8
            )
            
            # Draw text with shadow
            draw.text((x1+8, y1-112), label, fill='#000000', font=font)
            draw.text((x1, y1-120), label, fill='#FF0000', font=font)
        
        return image
    
    def is_caption(self, text, region_type=None):
        """Check if the text matches caption patterns for a specific region type."""
        if not text:
            return False
        
        text = text.strip()
        
        # If region type is specified, only check for that type
        if region_type and region_type in self.caption_regex:
            return bool(self.caption_regex[region_type].match(text))
        
        # Otherwise check all types
        return any(bool(regex.match(text)) for regex in self.caption_regex.values())

    def get_caption_type(self, text):
        """Determine the type of caption (figure, table, or map)."""
        text = text.strip().lower()
        for caption_type, patterns in self.caption_patterns.items():
            if any(re.match(pattern, text, re.IGNORECASE) for pattern in patterns):
                return caption_type
        return None

    def extract_text_from_region(self, image, bbox):
        """Extract text from a region using OCR."""
        try:
            x1, y1, x2, y2 = map(int, bbox)
            region = image.crop((x1, y1, x2, y2))
            text = pytesseract.image_to_string(region)
            return text.strip()[:200] # Limit text length for practicality
        except Exception as e:
            logger.error(f"Error extracting text from region: {str(e)}")
            return ""

    def find_nearest_region(self, caption_bbox, regions, caption_type, search_above=True):
        """Find the nearest valid region to a caption based on type."""
        if not regions:
            return None

        caption_y = (caption_bbox[1] + caption_bbox[3]) / 2
        min_distance = float('inf')
        nearest_region = None

        valid_types = self.valid_region_types.get(caption_type, [])

        for region in regions:
            # Skip if region type doesn't match caption type
            if valid_types and region['label'].lower() not in valid_types:
                continue

            region_y = (region['bbox'][1] + region['bbox'][3]) / 2
            distance = abs(region_y - caption_y)

            # Check if region is in the correct direction
            if search_above and region_y < caption_y:
                if distance < min_distance:
                    min_distance = distance
                    nearest_region = region
            elif not search_above and region_y > caption_y:
                if distance < min_distance:
                    min_distance = distance
                    nearest_region = region

        return nearest_region

    def associate_caption_with_region(self, caption, regions):
        """Associate a caption with the nearest appropriate region."""
        caption_bbox = caption['bbox']
        caption_type = self.get_caption_type(caption['text'])
        
        if not caption_type:
            return False

        # First try to find a region above the caption
        nearest_region = self.find_nearest_region(
            caption_bbox, 
            regions, 
            caption_type, 
            search_above=True
        )

        # If no region found above, look for a region below
        if not nearest_region:
            nearest_region = self.find_nearest_region(
                caption_bbox, 
                regions, 
                caption_type, 
                search_above=False
            )

        if nearest_region:
            # Update the region with caption information
            nearest_region['caption'] = caption['text']
            nearest_region['caption_type'] = caption_type
            nearest_region['caption_bbox'] = caption_bbox
            return True
        return False

    def save_image_caption_metadata(self, regions):
        """Save metadata specifically for image-caption pairs."""
        image_caption_pairs = []
        
        for region in regions:
            if region['label'].lower() in ['figure', 'image', 'picture'] and 'caption' in region:
                pair_data = {
                    'region_number': region['number'],
                    'image_path': str(self.label_dirs['images'] / f"region_{region['number']}.png"),
                    'caption_path': str(self.label_dirs['captions'] / f"caption_{region['number']}.txt"),
                    'caption_text': region['caption'],
                    'caption_type': region.get('caption_type', 'unknown'),
                    'bbox': region['bbox'],
                    'position': region['position'],
                    'timestamp': datetime.now().isoformat()
                }
                image_caption_pairs.append(pair_data)
        
        # Save the image-caption pairs metadata
        metadata_path = self.label_dirs['metadata'] / 'image_caption_pairs.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_pairs': len(image_caption_pairs),
                'pairs': image_caption_pairs,
                'timestamp': datetime.now().isoformat()
            }, f, indent=4)
        
        logger.info(f"Saved {len(image_caption_pairs)} image-caption pairs metadata to {metadata_path}")

    def save_caption_text(self, region):
        """Save caption text with additional metadata."""
        if 'caption' in region:
            caption_data = {
                'region_number': region['number'],
                'caption_text': region['caption'],
                'caption_type': region.get('caption_type', 'unknown'),
                'associated_region': {
                    'label': region['label'],
                    'bbox': region['bbox'],
                    'position': region['position']
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Save caption text file
            caption_path = self.label_dirs['captions'] / f"caption_{region['number']}.txt"
            with open(caption_path, 'w', encoding='utf-8') as f:
                f.write(region['caption'])
            
            # Save caption metadata
            caption_metadata_path = self.label_dirs['captions'] / f"caption_{region['number']}_metadata.json"
            with open(caption_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(caption_data, f, indent=4)
            
            return caption_path, caption_metadata_path
        return None, None

    def save_cropped_regions_metadata(self, regions):
        """Save metadata for cropped regions by type (image, text, table)."""
        # Initialize metadata structure
        regions_by_type = {
            'images': [],
            'text': [],
            'tables': []
        }
        
        for region in regions:
            region_data = {
                'region_number': region['number'],
                'label': region['label'],
                'bbox': region['bbox'],
                'position': region['position'],
                'image_path': str(self.label_dirs[region['label'].lower()] / f"region_{region['number']}.png"),
                'has_caption': 'caption' in region,
                'caption_text': region.get('caption', ''),
                'caption_type': region.get('caption_type', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            # Categorize region
            if region['label'].lower() in ['figure', 'image', 'picture']:
                regions_by_type['images'].append(region_data)
            elif region['label'].lower() == 'text':
                regions_by_type['text'].append(region_data)
            elif region['label'].lower() == 'table':
                regions_by_type['tables'].append(region_data)
        
        # Save metadata for each type
        for region_type, regions_list in regions_by_type.items():
            if regions_list:  # Only save if there are regions of this type
                # Save in metadata directory
                metadata_path = self.label_dirs['metadata'] / f"{region_type}_regions.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'type': region_type,
                        'total_regions': len(regions_list),
                        'regions': regions_list,
                        'timestamp': datetime.now().isoformat()
                    }, f, indent=4)
                
                # Also save in json_output directory
                json_output_path = self.label_dirs['json_output'] / f"{region_type}_regions.json"
                with open(json_output_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'type': region_type,
                        'total_regions': len(regions_list),
                        'regions': regions_list,
                        'timestamp': datetime.now().isoformat()
                    }, f, indent=4)
                
                logger.info(f"Saved {len(regions_list)} {region_type} regions metadata to {metadata_path} and {json_output_path}")

def render_page_to_image(page, dpi=200):
    """Convert a PDF page to an image."""
    try:
        zoom = dpi / 72  # 72 is default dpi
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("ppm")
        return Image.open(BytesIO(img_bytes))
    except Exception as e:
        logger.error(f"Error rendering page: {str(e)}")
        raise

def process_pdf(pdf_path, dpi=200, max_workers=4):
    """Process a single PDF file and return its pages as images."""
    try:
        logger.info(f"Processing PDF: {pdf_path}")
        doc = fitz.open(pdf_path)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            images = list(executor.map(lambda page: render_page_to_image(page, dpi), doc))
        logger.info(f"Successfully processed {len(images)} pages from PDF")
        return images
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
        raise

def process_image(image_path):
    """Process a single image file."""
    try:
        logger.info(f"Processing image: {image_path}")
        img = Image.open(image_path)
        logger.info(f"Successfully processed image")
        return [img]  # Return as list for consistency with PDF processing
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {str(e)}")
        raise

def process_files(file_paths, dpi=200, max_workers=4, processor=None):
    """Process multiple files (PDFs and images) and return their images and updated processor."""
    all_images = []
    # Use provided processor instance or create a new one
    if processor is None:
        processor = LayoutProcessor()

    processor.regions_by_page = [] # Initialize regions_by_page attribute

    for file_path in file_paths:
        if file_path.lower().endswith('.pdf'):
            images = process_pdf(file_path, dpi, max_workers)
        else:
            images = process_image(file_path)
        all_images.extend(images)

    # Process each image (page) and store regions in the processor instance
    for image in all_images:
        regions_on_page, _ = process_single_page(image, processor)
        processor.regions_by_page.append(regions_on_page)

    return all_images, processor # Return images and the fully updated processor instance

def extract_layout_info(layout_predictions):
    """Extract layout information from Surya model predictions."""
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

def process_page_layout(page_image, layout_predictions, processor):
    """Process a single page's layout and identify regions of interest."""
    # Get layout information
    layout_info = extract_layout_info(layout_predictions)
    
    # Sort by position to maintain reading order
    layout_info.sort(key=lambda x: x['position'])
    
    # First pass: identify all regions and potential captions
    regions = []
    captions = []
    
    # Ensure statistics structure is ready
    if not hasattr(processor, 'statistics'):
        processor.statistics = {
            'total_regions': 0,
            'regions_by_type': {},
            'captions_by_type': {}
        }
    if 'total_regions' not in processor.statistics:
        processor.statistics['total_regions'] = 0
    if 'regions_by_type' not in processor.statistics:
        processor.statistics['regions_by_type'] = {}
    if 'captions_by_type' not in processor.statistics:
        processor.statistics['captions_by_type'] = {}

    for element in layout_info:
        x1, y1, x2, y2 = element['bbox']
        label = element['label'].lower()
        position = element['position']
        
        # Extract text from the region
        text = processor.extract_text_from_region(page_image, (x1, y1, x2, y2))
        
        # Check if this is a caption
        if processor.is_caption(text):
            caption_data = {
                'text': text,
                'bbox': (x1, y1, x2, y2),
                'position': position
            }
            captions.append(caption_data)
            continue
        
        # Only process valid region types and update statistics
        if label in ['table', 'figure', 'image', 'picture', 'map', 'text']:
            # Increment region counter
            processor.region_counter += 1
            
            # Store region information
            region_data = {
                'number': processor.region_counter,
                'label': label,
                'position': position,
                'bbox': (x1, y1, x2, y2),
                'region_type': label,
                'timestamp': datetime.now().isoformat()
            }
            regions.append(region_data)
            
            # Update instance statistics
            region_type = 'image' if label in ['figure', 'image', 'picture'] else label
            # Ensure the region type key exists in statistics
            if 'regions_by_type' not in processor.statistics:
                 processor.statistics['regions_by_type'] = {}
            if region_type not in processor.statistics['regions_by_type']:
                 processor.statistics['regions_by_type'][region_type] = 0
            
            processor.statistics['total_regions'] += 1
            processor.statistics['regions_by_type'][region_type] += 1
    
    # Second pass: associate captions with regions and update statistics
    for caption in captions:
        if processor.associate_caption_with_region(caption, regions):
            caption_type = processor.get_caption_type(caption['text'])
            if caption_type:
                 # Ensure the caption type key exists in statistics
                 if 'captions_by_type' not in processor.statistics:
                     processor.statistics['captions_by_type'] = {}
                 if caption_type not in processor.statistics['captions_by_type']:
                     processor.statistics['captions_by_type'][caption_type] = 0

                 processor.statistics['captions_by_type'][caption_type] += 1

    
    return regions

def save_cropped_regions(image, regions, processor):
    """Save cropped regions into appropriate folders based on their labels."""
    try:
        # Convert image to numpy array if it's a PIL Image
        if isinstance(image, Image.Image):
            image = np.array(image)
        
        # Ensure statistics structure is ready
        if not hasattr(processor, 'statistics'):
            processor.statistics = {
                'total_regions': 0,
                'regions_by_type': {},
                'captions_by_type': {}
            }

        # Process each region
        for region in regions:
            try:
                # Get region coordinates
                x1, y1, x2, y2 = map(int, region['bbox'])
                
                # Ensure coordinates are within image bounds
                height, width = image.shape[:2]
                x1 = max(0, min(x1, width))
                y1 = max(0, min(y1, height))
                x2 = max(0, min(x2, width))
                y2 = max(0, min(y2, height))
                
                # Crop the region
                region_image = image[y1:y2, x1:x2]
                
                # Convert to PIL Image for saving
                region_pil = Image.fromarray(region_image)
                
                # Determine the appropriate folder based on label
                label = region['label'].lower()
                if label in ['figure', 'image', 'picture']:
                    folder = processor.label_dirs['figures']
                elif label == 'table':
                    folder = processor.label_dirs['tables']
                elif label == 'map':
                    folder = processor.label_dirs['maps']
                else:
                    folder = processor.label_dirs['text']
                
                # Create folder if it doesn't exist
                folder.mkdir(parents=True, exist_ok=True)
                
                # Save the cropped image with region number
                output_path = folder / f"region_{region['number']}.png"
                region_pil.save(output_path)
                
                # Update region with image path
                region['image_path'] = str(output_path)
                
                # Save caption text and metadata if present
                if 'caption' in region:
                    caption_path, caption_metadata_path = processor.save_caption_text(region)
                    if caption_path and caption_metadata_path:
                        logger.info(f"Saved caption text to {caption_path}")
                        logger.info(f"Saved caption metadata to {caption_metadata_path}")
                
                # Save individual metadata file for the region
                metadata_path = processor.save_region_metadata(region)
                
                logger.info(f"Saved {label} region {region['number']} to {output_path}")
                logger.info(f"Saved metadata to {metadata_path}")
                
            except Exception as region_error:
                logger.error(f"Error processing region {region.get('number', 'unknown')}: {str(region_error)}")
                continue
        
        # Save type-specific metadata
        processor.save_type_metadata(regions)
        
        # Save image-caption pairs metadata
        processor.save_image_caption_metadata(regions)
        
        # Save cropped regions metadata by type
        processor.save_cropped_regions_metadata(regions)
        
        # Draw labels and captions on the original image
        labeled_image = processor.draw_region_labels(Image.fromarray(image), regions)
        
        # Save the labeled image
        labeled_image_path = processor.base_output_dir / 'labeled_images'
        labeled_image_path.mkdir(exist_ok=True)
        labeled_image.save(labeled_image_path / f"labeled_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        return labeled_image
            
    except Exception as e:
        logger.error(f"Error saving regions: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def process_single_page(page_image, processor):
    """Process a single page through the layout model and return its regions."""
    if layout_predictor is None:
        raise ImportError("Surya model not found. Please install it using: pip install surya")
        
    try:
        # Check if page_image is already a PIL Image
        if not isinstance(page_image, Image.Image):
            pil_image = Image.fromarray(page_image)
        else:
            pil_image = page_image
        
        # Get layout predictions
        layout_predictions = layout_predictor([pil_image])
        
        # Process the page (this updates processor.statistics)
        # Do not save regions or metadata here, that will be done in process_files
        regions = process_page_layout(pil_image, layout_predictions, processor)
        
        # process_single_page should return regions for this page
        return regions, None # Return regions and None for labeled_image as saving is done later
        
    except Exception as e:
        logger.error(f"Error processing page: {str(e)}")
        logger.error(traceback.format_exc())
        # Propagate the exception after logging
        raise

if __name__ == "__main__":
    # This will be handled by the GUI
    pass
