import json
import os
import glob
from pathlib import Path

def process_json_file(input_file_path, solr_output_dir, docs_output_dir):
    """Process a single JSON file and create Solr and docs outputs"""
    
    try:
        # Load the original JSON data
        with open(input_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        solr_docs = []
        
        for page in data['pages']:
            # Combine OCR text from regions NOT in excluded list
            combined_text_ocr = []
            
            # Store all region information (except Text regions)
            all_regions_data = []
            
            for region in page['regions']:
                # Store all region data (except for regions with label "Text")
                if region.get('label') != "Text":
                    region_data = {
                        "region_id": region.get('region_id'),
                        "label": region.get('label', ''),
                        "position": region.get('position', 0),
                        "image_size": region.get('image_size', []),
                        "ocr_text": region.get('ocr_text', ''),
                        "captions": region.get('captions', ''),
                        "description": region.get('description', '')
                    }
                    all_regions_data.append(region_data)
                
                # Combine OCR text from regions NOT in the excluded list
                excluded_labels = ['figure', 'image', 'picture', 'table', 'map', 'Figure', 'photograph', 'site layout']
                
                if region.get('label') not in excluded_labels:
                    ocr_text = region.get('ocr_text', '').strip()
                    if ocr_text:
                        combined_text_ocr.append(ocr_text)
            
            # Create page-level document
            doc = {
                "id": f"{data['pdf_path'].split('/')[-1]}_page{page['page_number']}",
                "pdf_path": data['pdf_path'],
                "total_pages": data['total_pages'],
                "page_number": page['page_number'],
                "page_url": page.get('page_url', ''),
                "combined_text_ocr": ' '.join(combined_text_ocr),  # Only non-excluded label OCR combined
                "all_regions": all_regions_data  # All region data preserved (except Text regions)
            }
            
            solr_docs.append(doc)
        
        # Create output filenames
        base_filename = Path(input_file_path).stem.replace('_pdf_metadata', '')
        
        # Save Solr format
        solr_output_path = os.path.join(solr_output_dir, f"{base_filename}_solr.json")
        with open(solr_output_path, 'w', encoding='utf-8') as f:
            json.dump({"add": {"doc": solr_docs}}, f, indent=2, ensure_ascii=False)
        
        # Save docs only format
        docs_output_path = os.path.join(docs_output_dir, f"{base_filename}_docs.json")
        with open(docs_output_path, 'w', encoding='utf-8') as f:
            json.dump(solr_docs, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Processed: {base_filename} - {len(solr_docs)} pages")
        return solr_docs  # Return the documents for combining
        
    except Exception as e:
        print(f"✗ Error processing {input_file_path}: {str(e)}")
        return None

def main():
    # Define paths
    base_dir = "/mnt/storage/TIE-corpus-parsed"
    solr_output_dir = os.path.join(base_dir, "solr_parsed_json")
    docs_output_dir = os.path.join(base_dir, "normal_parsed_json")
    
    # Create output directories if they don't exist
    os.makedirs(solr_output_dir, exist_ok=True)
    os.makedirs(docs_output_dir, exist_ok=True)
    
    # Find all metadata JSON files
    pattern = os.path.join(base_dir, "*/metadata/*_pdf_metadata.json")
    json_files = glob.glob(pattern)
    
    if not json_files:
        print("No JSON metadata files found!")
        print(f"Search pattern: {pattern}")
        return
    
    print(f"Found {len(json_files)} JSON files to process...")
    print("-" * 60)
    
    # Process each file and collect all documents
    successful = 0
    failed = 0
    all_solr_docs = []  # Collect all documents for combined file
    
    for json_file in json_files:
        result = process_json_file(json_file, solr_output_dir, docs_output_dir)
        if result:
            successful += 1
            # Add the returned documents to the combined list
            all_solr_docs.extend(result)
        else:
            failed += 1
    
    # Create combined Solr JSON file
    if all_solr_docs:
        combined_solr_path = os.path.join(base_dir, "combined_solr_all_documents.json")
        with open(combined_solr_path, 'w', encoding='utf-8') as f:
            json.dump({"add": {"doc": all_solr_docs}}, f, indent=2, ensure_ascii=False)
        
        combined_docs_path = os.path.join(base_dir, "combined_docs_all_documents.json")
        with open(combined_docs_path, 'w', encoding='utf-8') as f:
            json.dump(all_solr_docs, f, indent=2, ensure_ascii=False)
        
        print("-" * 60)
        print(f"✓ Created combined files with {len(all_solr_docs)} total documents")
        print(f"Combined Solr: {combined_solr_path}")
        print(f"Combined Docs: {combined_docs_path}")
    
    print("-" * 60)
    print(f"Processing complete!")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"Individual Solr files: {solr_output_dir}")
    print(f"Individual Docs files: {docs_output_dir}")

if __name__ == "__main__":
    main()
