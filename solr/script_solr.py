import json
import pysolr

# Configuration: Update these values before running
SOLR_HOST = "http://localhost:8000/solr"
TEXT_CORE_NAME = "text-corpus"
TABLES_CORE_NAME = "table-corpus"
IMAGES_CORE_NAME = "image-corpus"

TEXT_JSON_PATH = r"/home/nivedita/night_test/solr/solr_metadata/text_corpus.json"
TABLES_JSON_PATH = r"/home/nivedita/night_test/solr/solr_metadata/table_corpus.json"
IMAGES_JSON_PATH = r"/home/nivedita/night_test/solr/solr_metadata/images_corpus.json"

# TEXT_JSON_PATH = 
# TABLES_JSON_PATH = 
# IMAGES_JSON_PATH = 

def index_core(solr_core_url: str, json_path: str) -> None:
    """
    Reads a JSON file (list of documents) and indexes them into the specified Solr core.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        docs = json.load(f)

    solr = pysolr.Solr(solr_core_url, always_commit=True, timeout=10)
    solr.add(docs)
    print(f"Indexed {len(docs)} documents into {solr_core_url}")

def main():
    # Build full core URLs
    text_core_url = f"{SOLR_HOST}/{TEXT_CORE_NAME}"
    tables_core_url = f"{SOLR_HOST}/{TABLES_CORE_NAME}"
    images_core_url = f"{SOLR_HOST}/{IMAGES_CORE_NAME}"

    # Index each JSON file into its respective core
    index_core(text_core_url, TEXT_JSON_PATH)
    index_core(tables_core_url, TABLES_JSON_PATH)
    index_core(images_core_url, IMAGES_JSON_PATH)

if __name__ == "__main__":
    main()
