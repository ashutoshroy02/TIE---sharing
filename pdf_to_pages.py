'''RETURNS A LIST OF PAGES OF PDF <FUNCTION PROCESS_FILE> .Converts the pdf to images and passes it to preprocessing .it stores the pages as a list and does not save on device .
 It handles any input pdf or images any kind . Also the DPI (Density per Inch) is set to 200 for better ocr task . 
 we can reduce it to faster the process but affect OCR quality'''

from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
import io
import magic
import os

def detect_file_type(file_input):
    if isinstance(file_input, Image.Image):
        return 'image'
    
    if isinstance(file_input, bytes):
        mime = magic.from_buffer(file_input, mime=True)
        if mime == 'application/pdf':
            return 'pdf'
        elif mime.startswith('image/'):
            return 'image'
        raise ValueError(f"Unsupported file type: {mime}")
    
    if isinstance(file_input, str):
        if not os.path.exists(file_input):
            raise FileNotFoundError(f"File not found: {file_input}")
        
        mime = magic.from_file(file_input, mime=True)
        if mime == 'application/pdf':
            return 'pdf'
        elif mime.startswith('image/'):
            return 'image'
        raise ValueError(f"Unsupported file type: {mime}")
    
    raise ValueError("Input must be a file path, bytes, or PIL Image")

def convert_to_pages(file_input, dpi=200):
    file_type = detect_file_type(file_input)
    
    if isinstance(file_input, bytes):
        input_buffer = io.BytesIO(file_input)
        if file_type == 'pdf':
            return convert_from_bytes(file_input, dpi=dpi, fmt='PIL')
        return [Image.open(input_buffer)]
            
    if isinstance(file_input, str):
        if file_type == 'pdf':
            return convert_from_path(file_input, dpi=dpi, fmt='PIL')
        return [Image.open(file_input)]
            
    if isinstance(file_input, Image.Image):
        return [file_input]

from PIL import Image

def process_file(file_path_or_bytes, dpi=200):
    file_type = detect_file_type(file_path_or_bytes)
    if file_type == 'pdf':
        pages = convert_to_pages(file_path_or_bytes, dpi=dpi)
    elif file_type == 'image':
        if isinstance(file_path_or_bytes, str):
            pages = [Image.open(file_path_or_bytes)]
        elif isinstance(file_path_or_bytes, bytes):
            pages = [Image.open(io.BytesIO(file_path_or_bytes))]
        elif isinstance(file_path_or_bytes, Image.Image):
            pages = [file_path_or_bytes]
        else:
            raise ValueError("Unsupported image input type.")
    else:
        raise ValueError("Invalid file input.")
    return pages


##to test

'''##display the pages for the pdf or an image
# file_path = r'book2-120-125.pdf'
file_path = r"Z:\TO DO\codes\IIT\ashu\model_output\original dataset\heading and two cloumn.png"
# result = process_file(file_path)

# for img in result:
#     img.show()
#     input()
#     img.close()

'''
