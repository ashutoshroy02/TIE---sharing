"""
Page-Level Metadata Processor: Processes PDF metadata and creates flattened, 
page-level dictionaries separated by content types (text, tables, figures) for Solr indexing.
"""
import json
import os
from typing import Dict, List, Any
import datetime

def process_page_metadata_for_solr(input_json_path: str, output_folder: str) -> None:
    """
    Process PDF metadata and create separate JSON files for text, tables, and figures
    with flattened page-level dictionaries suitable for Solr indexing.
    
    Args:
        input_json_path: Path to the input JSON file containing page metadata
        output_folder: Directory to save the separated metadata files
    """
    
    # Read the input JSON data
    with open(input_json_path, 'r',encoding="utf-8") as f:
        pages_data = json.load(f)
    
    # Initialize lists to store page-level dictionaries
    text_pages = []
    table_pages = []
    figure_pages = []
    
    # Process each page
    for page_data in pages_data:
        pdf_path = page_data.get('pdf_path', '')
        page_number = page_data.get('page_number', 0)
        page_url = page_data.get('page_url', '')
        combined_text_ocr = page_data.get('combined_text_ocr', '')
        
        # Track if page has content of each type
        has_text_content = False
        has_table_content = False
        has_figure_content = False
        
        # Process all regions in the page
        for region in page_data.get('all_regions', []):
            label = region.get('label', '').lower()
            
            # Text content (including headers, paragraphs, etc.)
            if label in ['text', 'title', 'header', 'footer', 'caption', 'paragraph', 'sectionheader']:
                if not has_text_content:
                    text_page = {
                        'id': f"{os.path.basename(pdf_path)}_page_{page_number}_text",
                        'pdf_url': pdf_path,
                        'page_url': page_url,
                        'page_number': page_number,
                        'ocr_combined_text': combined_text_ocr
                    }
                    text_pages.append(text_page)
                    has_text_content = True
            
            # Table content
            elif label == 'table':
                if not has_table_content:
                    # For tables, we use the page_url as table_url since individual table images aren't specified
                    table_page = {
                        'id': f"{os.path.basename(pdf_path)}_page_{page_number}_table",
                        'pdf_url': pdf_path,
                        'page_url': page_url,
                        'table_url': page_url,  # Using page_url as table_url
                        'page_number': page_number,
                        'description': region.get('description', ''),
                        'captions': region.get('captions', ''),
                        'ocr_text': region.get('ocr_text', ''),
                        'padded_bbox': region.get('padded_bbox', [])
                    }
                    table_pages.append(table_page)
                    has_table_content = True
            
            # Figure/Picture content
            elif label in ['figure', 'image', 'picture']:
                if not has_figure_content:
                    # For figures, we use the page_url as picture_url since individual figure images aren't specified
                    figure_page = {
                        'id': f"{os.path.basename(pdf_path)}_page_{page_number}_figure",
                        'pdf_url': pdf_path,
                        'page_url': page_url,
                        'picture_url': page_url,  # Using page_url as picture_url
                        'page_number': page_number,
                        'padded_bbox': region.get('padded_bbox', []),
                        'description': region.get('description', ''),
                        'captions': region.get('captions', ''),
                        'ocr_text': region.get('ocr_text', '')
                    }
                    figure_pages.append(figure_page)
                    has_figure_content = True
        
        # If page has no regions but has combined_text_ocr, add it as text content
        if not page_data.get('all_regions', []) and combined_text_ocr.strip():
            text_page = {
                'id': f"{os.path.basename(pdf_path)}_page_{page_number}_text",
                'pdf_url': pdf_path,
                'page_url': page_url,
                'page_number': page_number,
                'ocr_combined_text': combined_text_ocr
            }
            text_pages.append(text_page)
    
    # Create output directory
    metadata_folder = os.path.join(output_folder, 'solr_metadata')
    os.makedirs(metadata_folder, exist_ok=True)
    
    # Save text metadata
    if text_pages:
        text_metadata_path = os.path.join(metadata_folder, 'text_corpus.json')
        with open(text_metadata_path, 'w') as f:
            json.dump(text_pages, f, indent=2)
        print(f"Saved {len(text_pages)} text pages to: {text_metadata_path}")
    
    # Save table metadata
    if table_pages:
        table_metadata_path = os.path.join(metadata_folder, 'table_corpus.json')
        with open(table_metadata_path, 'w') as f:
            json.dump(table_pages, f, indent=2)
        print(f"Saved {len(table_pages)} table pages to: {table_metadata_path}")
    
    # Save figure metadata
    if figure_pages:
        figure_metadata_path = os.path.join(metadata_folder, 'images_corpus.json')
        with open(figure_metadata_path, 'w') as f:
            json.dump(figure_pages, f, indent=2)
        print(f"Saved {len(figure_pages)} figure pages to: {figure_metadata_path}")
    
    # Print summary
    print(f"\nProcessing Summary:")
    print(f"Total pages processed: {len(pages_data)}")
    print(f"Text pages: {len(text_pages)}")
    print(f"Table pages: {len(table_pages)}")
    print(f"Figure pages: {len(figure_pages)}")
    
    return text_metadata_path, table_metadata_path , figure_metadata_path

def split_into_3(input_json_path,output_folder):
    """
    Main function to process the metadata files.
    """ 
    try:
        text_json_path, table_json_path, image_json_path = process_page_metadata_for_solr(input_json_path, output_folder)
        print("\nMetadata processing completed successfully!")
    except FileNotFoundError:
        print(f"Error: Input file '{input_json_path}' not found.")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in input file. {e}")
    except Exception as e:
        print(f"Error: An unexpected error occurred. {e}")

    return text_json_path, table_json_path, image_json_path

if __name__ == "__main__":
    split_into_3("/mnt/storage/TIE-corpus-parsed/combined_docs_all_documents.json","/home/nivedita/night_test/solr")