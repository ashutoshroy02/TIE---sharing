import json
import os
import glob
from pathlib import Path

def process_json_file(input_file_path):
    """Process a single JSON files and docs outputs"""
    
    try:
        # Load the original JSON data
        with open(input_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        docs = []
        
        for page in data['pages']:
            # Combine OCR text from regions NOT in excluded list
            combined_text_ocr = []
       # Store all region information (except Text regions)
            all_regions_data = []
            
            excluded_labels = ['figure', 'image', 'Image','picture','Picture' ,'table', 'Table' ,'map','Map' ,'Figure', 'photograph', 'site layout']
            for region in page['regions']:
                # Store all region data (except for regions with label "Text")
                if region.get('label').lower() in excluded_labels:
                    region_data = {
                        "label": region.get('label', ''),
                        "position": region.get('position', 0),
                        "padded_bbox": region.get('padded_bbox', []),
                        "ocr_text": region.get('ocr_text', ''),
                        "captions": region.get('captions', ''),
                        "description": region.get('description', ''),
                        "cropped_pic_path": region.get('saved_path', '')
                    }
                    
                    all_regions_data.append(region_data)
                # print(f"All region data: {all_regions_data}")
                # Combine OCR text from regions NOT in the excluded list
                
                if region.get('label') == "Text":
                    ocr_text = region.get('ocr_text', '').strip()
                    if ocr_text:
                        combined_text_ocr.append(ocr_text + '\n')
            
            # Create page-level document
            doc = {
                "id": f"{data['pdf_path'].split('/')[-1]}_page{page['page_number']}",
                "pdf_path": data['pdf_path'],
                "page_number": page['page_number'],
                "page_url": page.get('page_url', ''),
                "combined_text_ocr": ''.join(combined_text_ocr),  # Only non-excluded label OCR combined
                "all_regions": all_regions_data  # All region data preserved (except Text regions)
            }
            
            docs.append(doc)
        
        return docs  # Return the documents for combining
        
    except Exception as e:
        print(f"✗ Error processing {input_file_path}: {str(e)}")
        return None

def process_folder(base_dir) 
    # Find all metadata JSON files
    all_files = []
    for root, dirs, files in os.walk(base_dir):
        # Remove unwanted directories in-place
        dirs[:] = [d for d in dirs if d not in ["testing", "Result","combined_corpus_parsed"]]
        for file in files:
            if file.endswith('.json'):
                all_files.append(os.path.join(root, file))
    # Now filter for *_pdf_metadata.json if you want only those
    json_files = [f for f in all_files if f.endswith('.json')]
    
    if not json_files:
        print("No JSON metadata files found!")
        return
    
    # print(f"Found {len(json_files)} JSON files to process...")
    # print("-" * 60)
    
    # Process each file and collect all documents
    successful = 0
    failed = 0
    all_docs = []  # Collect all documents for combined file
    
    for json_file in json_files:
        result = process_json_file(json_file)
        if result:
            successful += 1
            # Add the returned documents to the combined list
            all_docs.extend(result)
        else:
            failed += 1
        # Create output directory
    metadata_folder = os.path.join(base_dir, 'combined_corpus_parsed')
    os.makedirs(metadata_folder, exist_ok=True)
    # Create combined JSON file
    if all_docs:
        combined_dir = os.path.join(base_dir, "combined_corpus_parsed")
        combined_docs_path = os.path.join(combined_dir, "combined_docs_all_documents.json")
        with open(combined_docs_path, 'w', encoding='utf-8') as f:
            json.dump(all_docs, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Created combined files with {len(all_docs)} total documents")
        print(f"Combined Docs: {combined_docs_path}")
    
    print("-" * 60)
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")

    return combined_docs_path
