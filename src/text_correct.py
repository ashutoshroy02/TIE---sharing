# from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# model_name = "TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForCausalLM.from_pretrained(model_name)

# pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=64)



def ocr_text_correction(text):
#     prompt = """
# You are an expert in archaeology and historical documents. Correct the following OCR text, fixing spelling, grammar, and restoring archaeological terms if possible.

# OCR: "The site of Kalibangan is famos for its plouged feilds and the Sarasvati river."
# Corrected: "The site of Kalibangan is famous for its ploughed fields and the Sarasvati river."

# OCR: "The Harappan civlization florished in the Indus vally."
# Corrected: "The Harappan civilization flourished in the Indus valley."

# OCR: "{}"
# Corrected:
# """.format(text)
#     result = pipe(prompt)[0]['generated_text']
#     # Extract the corrected text after "Corrected:"
#     corrected = result.split("Corrected:")[-1].strip().split("\n")[0]

    return text

def generate_description_region(page_metadata_list, caption):
    description_texts = []
    for page_metadata in page_metadata_list:
        # Get all regions above (with lower position), sorted by position (top to bottom)
        page_metadata = page_metadata['regions']
        #page_metadata = [r for r in page_metadata if r['label'] == 'Text']
        description_texts = []
        for region in page_metadata:
            if region.get('label', '').lower() == 'Text':
                if caption in region.get('ocr_text', ''):
                    description_texts.append(region['ocr_text'])

    description = " ".join(description_texts)
    print(f"Generated description: {description}")
    return description

def generate_description(page_metadata_list, caption):
    """
    For each region in page_metadata['regions'],
    - if label in ['image', 'table', 'picture', 'figure'], set 'description' to generate_description_region(page_metadata)
    - else, set 'description' to ''
    Returns the updated page_metadata dict .
    The description is limited to 300 characters.
    """
    for page_metadata in page_metadata_list:
        if not page_metadata or 'regions' not in page_metadata or page_metadata['regions'] is None:
            continue  # Skip empty or malformed metadata
        regions = page_metadata['regions']
        for region in regions:
            label = region.get('label', '').lower()
            if label in ['image', 'table', 'picture', 'figure']:
                # Generate description for this region
                try:
                    description = generate_description_region(page_metadata_list, caption)
                except Exception as e:
                    description = region.get('ocr_text', '')
                # Limit to 300 characters
                if len(description) > 300:
                    description = description[:297] + '.'
                region['description'] = description
            else:
                region['description'] = ''
    return page_metadata
