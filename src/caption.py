'''captions from figures , maps and Tables are extracted from the page'''
''' we used heusrestics methods to come up with this'''

import re

# --- Caption Patterns and Regex ---
CAPTION_PATTERNS = {
    'figure': [
        r'^(?:Fig\.?|Figure\.?|FIGURE|FIG)\s*\d+[A-Z]?[.:]?\s*',
        r'^(?:Fig|Figure)\s*\d+\s*\([A-Z]\)\s*',
        r'^(?:Fig|Figure)\s*\d+\s*[\-–]\s*\d+[.:]?\s*',
        r'^(?:Fig|Figure)\s*\d+\s*(?:and|to)\s*\d+[.:]?\s*',
        r'^Illustration\s*\d+[.:]?\s*',
        r'^Plate\s*\d+[.:]?\s*',
        r'^Figure\s*[:.-]?\s*$',                       # "Figure:"
        r'^(?:Figure|Fig)\s*\(?[ivxIVX]+\)?[.:]?\s*'    # Roman numerals
    ],
    'table': [
        r'^(?:Table\.?|Tbl\.?|TABLE|TBL)\s*\d+[A-Z]?[.:]?\s*',
        r'^(?:Table)\s*\d+\s*\([A-Z]\)[.:]?\s*',
        r'^(?:Table)\s*\d+\s*[\-–]\s*\d+[.:]?\s*',
        r'^(?:Table)\s*\d+\s*(?:and|to)\s*\d+[.:]?\s*',
        r'^Tabular\s*data\s*\d*[.:]?\s*',
        r'^Data\s*Table\s*\d*[.:]?\s*',
        r'^Table\s*[:.-]?\s*$',                        # "Table:"
        r'^Table\s*\(?[ivxIVX]+\)?[.:]?\s*',                 # Roman numerals
        r'^(?:Table\.?|Tbl\.?|TABLE|TBL)\s*[:.-]\s+.+',
    ],
    'map': [
        r'^(?:Map\.?|MAP)\s*\d+[.:]?\s*',
        r'^Sketch\s*Map\s*\d*[.:]?\s*',
        r'^Location\s*Map\s*\d*[.:]?\s*',
        r'^Topographic\s*Map\s*\d*[.:]?\s*',
        r'^Map\s*\d+\s*[\-–]\s*\d+[.:]?\s*',
        r'^Map\s*[:.-]?\s*$',                          # "Map:"
        r'^Map\s*\(?[ivxIVX]+\)?[.:]?\s*'              # Roman numerals
    ]
}


CAPTION_REGEX = {
    k: re.compile('|'.join(f'(?:{p})' for p in v), re.IGNORECASE)
    for k, v in CAPTION_PATTERNS.items()
}
# VALID_REGION_TYPES = {
#     'figure': ['figure', 'image', 'picture'],
#     'table': ['table'],
#     'map': ['map']
# }

# --- Helper Functions ---

def extract_caption_contained_within(text, region_type=None):
    if not text:
        return False
    text = re.sub(r'\s+', ' ', text.strip())
    # If region_type is a figure/image-like label, check if text contains a caption pattern anywhere
    if region_type and region_type.lower() in ['figure', 'image', 'picture', 'fig', 'table', 'map']:
        for pattern in CAPTION_PATTERNS.get(region_type.lower(), []):
            pattern_no_anchor = pattern[1:] if pattern.startswith('^') else pattern
            match = re.search(pattern_no_anchor, text)
            if match:
                end_pos = text.find('<', match.end())
                if end_pos == -1:
                    extracted_text = text[match.start():]
                else:
                    extracted_text = text[match.start():end_pos]
                return extracted_text.strip()
    return None

def is_caption(text, region_type=None):
    if not text:
        return False
    text = re.sub(r'\s+', ' ', text.strip())
    if region_type and region_type in CAPTION_REGEX:
        return bool(CAPTION_REGEX[region_type].match(text))
    return any(bool(regex.match(text)) for regex in CAPTION_REGEX.values())

# def get_caption_type(text):
#     text = re.sub(r'\s+', ' ', text.strip())
#     for caption_type, patterns in CAPTION_PATTERNS.items():
#         if any(re.match(pattern, text, re.IGNORECASE) for pattern in patterns):
#             return caption_type
#     return None

def find_nearest_region(caption_bbox, regions, search_above=True):
    caption_y = (caption_bbox[1] + caption_bbox[3]) / 2
    min_distance = float('inf')
    nearest_region = None
    valid_labels = {"table", "image", "picture","figure"}
    for region in regions:
        label = region['label'].lower() 
        if label not in valid_labels:
            continue
        region_y = (region['original_bbox'][1] + region['original_bbox'][3]) / 2 \
            if 'original_bbox' in region else (region['bbox'][1] + region['bbox'][3]) / 2
        distance = abs(region_y - caption_y)
        if search_above and region_y < caption_y:
            if distance < min_distance:
                min_distance = distance
                nearest_region = region
        elif not search_above and region_y > caption_y:
            if distance < min_distance:
                min_distance = distance
                nearest_region = region
    return nearest_region


def process_page_for_captions(page, page_num):
    regions = page['regions']
    caption_candidates = []



    for region in regions:
        text = region.get('ocr_text', '').strip()
        label = region.get('label', '')
        is_cap = is_caption(text, region_type=label)
        caption = extract_caption_contained_within(text, region_type=label)
        if caption:
            region['captions'] = caption
            continue
        if is_cap:
            print(f"→ Caption matched by regex: '{text}'")
            print("Caption: ", text)
            caption_candidates.append({
                'text': text,
                'bbox': region.get('padded_bbox') or region.get('bbox'),
                'position': region.get('position', 0)
            })
        '''else:
            # Fallback caption
            if label in ['figure', 'image', 'Picture', 'fig','Figure', 'Picture']:
                fallback_caption = 'Figure:'
            elif label in ['table', 'tbl', 'Table']:
                fallback_caption = 'Table:'
            elif label == ['Map', 'map', 'Image']:
                fallback_caption = 'Map:'
            else:
                fallback_caption = None

            if fallback_caption:
                caption_text = f"{fallback_caption} (page: {page_num})"
                # print(f"→ Using fallback caption: '{caption_text}' for label='{label}'")
                caption_candidates.append({
                    'text': text,
                    'bbox': region.get('padded_bbox') or region.get('bbox'),
                    'position': region.get('position', 0)
                })'''

    for caption in caption_candidates:

        nearest = find_nearest_region(caption['bbox'], regions ,search_above=True)
        if not nearest:
            nearest = find_nearest_region(caption['bbox'], regions ,search_above=False)

        if nearest:
            # print(f"✅ Caption '{caption['text']}' associated with region label='{nearest['label']}'")
            nearest['captions'] = caption['text']
        else:
            # print(f"❌ No nearby region found for caption: '{caption['text']}'")
            pass

    return page
