import sys
import os
from ocr_processor import process_pdf
    
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

pdf_folder = "/mnt/storage/nivedita/final_corpus"

# pdf_folder = "/home/nivedita/night_test"    
pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
print(f"Number of PDF files in '{pdf_folder}': {len(pdf_files)}")
for idx, pdf_file in enumerate(pdf_files, start=1):
    pdf_path = os.path.join(pdf_folder, pdf_file)
    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
    output_folder = os.path.join('/mnt/storage/TIE-corpus-parsed', pdf_basename)
    metadata_file = os.path.join(output_folder, 'metadata', f'{pdf_basename}_pdf_metadata.json')
    if os.path.exists(metadata_file):
        print(f"Skipping already processed PDF: {pdf_path}")
        continue
    #main process
    print(f"Processing PDF: {pdf_path}")
    process_pdf(pdf_path, output_folder )
