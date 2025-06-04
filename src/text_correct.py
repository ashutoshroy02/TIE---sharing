def generate_description_region(prev_page_metadata, current_page_metadata, next_page_metadata, cropped_caption):
    description_texts = []

    # Collect all regions from the three pages
    all_regions = []
    if prev_page_metadata and 'regions' in prev_page_metadata:
        all_regions.extend(prev_page_metadata['regions'])
    if current_page_metadata and 'regions' in current_page_metadata:
        all_regions.extend(current_page_metadata['regions'])
    if next_page_metadata and 'regions' in next_page_metadata:
        all_regions.extend(next_page_metadata['regions'])

    # print("Total regions collected:", len(all_regions))

    # Filter and check regions
    for idx, region in enumerate(all_regions):
        # print(f"Checking region {idx}, label: {region.get('label')}")
        if region.get('label', '').lower() == 'text':
            ocr = region.get('ocr_text', '')
            # print("OCR text:", ocr)
            if cropped_caption in ocr:
                # print("cropped_caption match found, adding to description.")
                description_texts.append(ocr)

    description = " ".join(description_texts)
    # print(f"Generated description: {description}")
    return description


def generate_description(prev_page_metadata, current_page_metadata, next_page_metadata, cropped_caption):
    # print("Generating descriptions for page:", current_page_metadata.get('page_number', 'Unknown'))

    if 'regions' not in current_page_metadata:
        # print("No 'regions' key in current_page_metadata!")
        return current_page_metadata

    regions = current_page_metadata['regions']
    for idx, region in enumerate(regions):
        label = region.get('label', '').lower()

        if label in ['image', 'table', 'picture', 'figure']:
            # print(f"Generating description for region {idx} with label '{label}'")
            try:
                description = generate_description_region(prev_page_metadata, current_page_metadata, next_page_metadata, cropped_caption)
            except Exception as e:
                # print(f"Error generating description: {e}")
                pass

            region['description'] = description
        else:
            region['description'] = ''

    return current_page_metadata
