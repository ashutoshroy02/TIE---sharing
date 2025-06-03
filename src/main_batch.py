import sys
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import glob
    
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

#pdf_folder = "/mnt/storage/nivedita/final_corpus"
pdf_folder = "../testing-documents"  # Change this to your PDF folder path
print(pdf_folder)

# pdf_folder = "/home/nivedita/night_test"    
pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
print(f"Number of PDF files in '{pdf_folder}': {len(pdf_files)}")

multiprocessing.set_start_method('spawn', force=True)

def process_single_pdf(pdf_path, output_folder):
    from ocr_processor import process_pdf
    print(f"Processing PDF: {pdf_path}")
    process_pdf(pdf_path, output_folder)

if __name__ == "__main__":
    tasks = []
    with ProcessPoolExecutor(max_workers=7) as executor:  # Adjust max_workers as needed
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_folder, pdf_file)
            pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
            #output_folder = os.path.join('/mnt/storage/TIE-corpus-parsed', pdf_basename)
            output_folder = os.path.join('output', pdf_basename)
            metadata_dir = os.path.join(output_folder, 'metadata')

            # Check if the output folder and metadata directory exist and metadata contains any .json files
            processed_already = False
            if os.path.isdir(output_folder) and os.path.isdir(metadata_dir):
                for entry in os.listdir(metadata_dir):
                    if entry.lower().endswith('.json'):
                        processed_already = True
                        break

            if processed_already:
                print(f"Skipping already processed PDF: {pdf_path}")
                continue

            tasks.append(executor.submit(process_single_pdf, pdf_path, output_folder))

        for future in as_completed(tasks):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing a PDF: {e}")
