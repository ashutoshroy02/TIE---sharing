'''
Metadata Processor: Separates the complete PDF metadata into different JSON files based on content types (text, tables, figures).
'''

import json
import os
from typing import Dict, List, Any
import datetime

def separate_metadata_by_type(complete_metadata: Dict[str, Any], output_folder: str) -> None:
    """
    Separate the complete PDF metadata into three different JSON files based on content types.
    
    Args:
        complete_metadata: The complete PDF metadata dictionary
        output_folder: Directory to save the separated metadata files
    """
    # Initialize metadata dictionaries for each type
    text_metadata = {
        'type': 'text',
        'pdf_path': complete_metadata['pdf_path'],
        'total_pages': complete_metadata['total_pages'],
        'processed_date': str(datetime.datetime.now()),
        'total_regions': 0,
        'pages': [],
        'caption': None,
        'description': []
    }
    
    tables_metadata = {
        'type': 'tables',
        'pdf_path': complete_metadata['pdf_path'],
        'total_pages': complete_metadata['total_pages'],
        'processed_date': str(datetime.datetime.now()),
        'total_regions': 0,
        'pages': [],
        'caption': None,
        'description': []
    }
    
    figures_metadata = {
        'type': 'figures',
        'pdf_path': complete_metadata['pdf_path'],
        'total_pages': complete_metadata['total_pages'],
        'processed_date': str(datetime.datetime.now()),
        'total_regions': 0,
        'pages': [],
        'caption': None,
        'description': []
    }
    
    # Process each page
    for page in complete_metadata['pages']:
        # Initialize page metadata for each type
        page_text = {
            'page_number': page['page_number'],
            'processed_date': page['processed_date'],
            'regions': []
        }
        
        page_tables = {
            'page_number': page['page_number'],
            'processed_date': page['processed_date'],
            'regions': []
        }
        
        page_figures = {
            'page_number': page['page_number'],
            'processed_date': page['processed_date'],
            'regions': []
        }
        
        # Separate regions by type
        for region in page['regions']:
            label = region['label'].lower()
            
            if label in ['text', 'title', 'header', 'footer', 'caption', 'paragraph']:
                page_text['regions'].append(region)
                text_metadata['total_regions'] += 1
            elif label == 'table':
                page_tables['regions'].append(region)
                tables_metadata['total_regions'] += 1
            elif label in ['figure', 'image', 'picture']:
                page_figures['regions'].append(region)
                figures_metadata['total_regions'] += 1
        
        # Add page metadata if it has regions
        if page_text['regions']:
            text_metadata['pages'].append(page_text)
        if page_tables['regions']:
            tables_metadata['pages'].append(page_tables)
        if page_figures['regions']:
            figures_metadata['pages'].append(page_figures)
    
    # Save the separated metadata files
    metadata_folder = os.path.join(output_folder, 'metadata')
    os.makedirs(metadata_folder, exist_ok=True)
    
    # Save text metadata
    text_metadata_path = os.path.join(metadata_folder, 'text_metadata.json')
    with open(text_metadata_path, 'w') as f:
        json.dump(text_metadata, f, indent=4)
    print(f"Saved text metadata to: {text_metadata_path}")
    
    # Save tables metadata
    tables_metadata_path = os.path.join(metadata_folder, 'tables_metadata.json')
    with open(tables_metadata_path, 'w') as f:
        json.dump(tables_metadata, f, indent=4)
    print(f"Saved tables metadata to: {tables_metadata_path}")
    
    # Save figures metadata
    figures_metadata_path = os.path.join(metadata_folder, 'figures_metadata.json')
    with open(figures_metadata_path, 'w') as f:
        json.dump(figures_metadata, f, indent=4)
    print(f"Saved figures metadata to: {figures_metadata_path}")

def process_metadata(complete_metadata_path: str, output_folder: str) -> None:
    """
    Process the complete PDF metadata file and separate it into different content types.
    
    Args:
        complete_metadata_path: Path to the complete PDF metadata JSON file
        output_folder: Directory to save the separated metadata files
    """
    try:
        # Read the complete metadata
        with open(complete_metadata_path, 'r') as f:
            complete_metadata = json.load(f)
        
        # Separate and save the metadata
        separate_metadata_by_type(complete_metadata, output_folder)
    except Exception as e:
        print(f"Error processing metadata file '{complete_metadata_path}': {e}")

if __name__ == "__main__":
    # Example usage
    output_folder = "output"  # Replace with your desired output folder
    folders = [name for name in os.listdir(output_folder) if os.path.isdir(os.path.join(output_folder, name))]
    print("Folders inside output_folder:", folders)
    for folder in folders:
        complete_metadata_path = os.path.join(output_folder, folder, "metadata", "complete_pdf_metadata.json")
        if os.path.exists(complete_metadata_path):
            process_metadata(complete_metadata_path, os.path.join(output_folder, folder))
        else:
            print(f"Metadata file not found for folder: {folder}")
