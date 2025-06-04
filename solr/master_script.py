from convert2solr import process_folder
from combined_to_2 import split_into_3


base_dir = "/mnt/storage/TIE-corpus-parsed"
#pdf combined
combined_docs = process_folder(base_dir)

#split into 3 for solr
output_folder = r"/home/nivedita/night_test/solr/"  # Output directory
text_json_path, table_json_path, image_json_path = split_into_3(input_json_path = combined_docs , output_folder)

#index in solr in 3 cores
