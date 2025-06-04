import pysolr
# import re
# import nltk
# from nltk.corpus import stopwords
# from nltk.stem import WordNetLemmatizer

# nltk.download('stopwords',quiet=True)
# nltk.download('wordnet',quiet=True)
# nltk.download('punkt',quiet=True)

# def preprocess_query(query):
#     """
#     Normalize and enrich the query to improve Solr keyword search compatibility.
#     """
#     query = query.lower()
#     query = re.sub(r'[^\w\s]', '', query)
#     words = nltk.word_tokenize(query)
#     stop_words = set(stopwords.words('english'))
#     words = [word for word in words if word not in stop_words]
#     lemmatizer = WordNetLemmatizer()
#     words = [lemmatizer.lemmatize(word) for word in words]
#     return ' '.join(words)


core_map = {
    "text": "text-corpus",
    "tables": "table-corpus",
    "images": "image-corpus"
}

def query_solr(core_choice, user_query, start=0, rows=5):
    core_name = core_map.get(core_choice)
    if not core_name:
        raise ValueError("Invalid core selected")

    # print(f"Debug: Using core: {core_name}")
    # print(f"Debug: Connecting to Solr URL: http://localhost:8983/solr/{core_name}")
    solr = pysolr.Solr(f'http://localhost:8983/solr/{core_name}', timeout=10)

    # Field boosts per core
    qf_map = {
        "text": "ocr_combined_text^1 ",
        "tables": "ocr_text^1 caption^2 description^1",
        "images": "description^1 ocr_text^1"
    }

    # Fields to return per core
    fl_map = {
        "text": "id,pdf_id,page_number,page_url,ocr_combined_text",
        "tables": "id,pdf_id,page_number,page_url,ocr_text,padded_bbox,caption,table_url",
        "images": "id,pdf_id,page_number,page_url,ocr_text, padded_bbox,caption,image_url"
    }

    # Build search parameters
    search_params = {
        "defType": "edismax",
        "qf": qf_map[core_choice],
        "fl": fl_map[core_choice],
        "start": start,
        "rows": rows
    }

    # Add df for the text core based on the image
    if core_choice == "text":
        search_params["df"] = "ocr_combined_text"

    # print(f"Debug: Search parameters: {search_params}")

    results = solr.search(user_query, **search_params)
    # print(f"Debug: Received {results.hits} hits from Solr.")
    parsed_results = []

    for doc in results.docs:
        parsed_results.append(doc)

    return {
        "results": parsed_results,
        "numFound": results.hits,
        "start": results.raw_response['response']['start']
    }

if __name__ == "__main__":
    try:
        core = input("Enter core choice (text, tables, images): ").lower()
        query = input("Enter your search query: ")
        # query = preprocess_query(query)
        
        # print(query)
        print("\nRunning search...")
        search_results = query_solr(core, query)
        print("\nSearch Results:")
        # print(f"Number of results found: {search_results['numFound']}")
        # Print a summary of results, or the full results if they are few
        for i, doc in enumerate(search_results['results']):
            print(f"Result {i+1}: {doc}")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
