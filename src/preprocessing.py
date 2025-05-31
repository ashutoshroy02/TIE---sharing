'''This code preprocess the page. 1. grayscale  2. denoise   3.thresh . overall it black and white the page .
Also removes the unwanted color. Enhances the text with 200 dpi . removes unawanted borders . 
Does not work for Shadow pages. if the page has a little shadow it darkens it very much'''

import cv2
import numpy as np
from pdf_to_pages import process_file

def preprocess_image(image):
    # Check if input is already numpy array
    if isinstance(image, np.ndarray):
        img = image
    else:
        # Convert PIL Image to OpenCV format
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Check if image is empty or has invalid dimensions
    if img is None or img.size == 0 or len(img.shape) != 3:
        # Return a blank image with same dimensions as input
        if isinstance(image, np.ndarray):
            return np.zeros_like(image)
        else:
            # If input was PIL Image, create a blank image with same size
            return np.zeros((image.height, image.width), dtype=np.uint8)
    
    # denoised =  cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 20)
    denoised  = cv2.bilateralFilter(img, 9, 75, 75)    #use any one if :: for higher qaulity for pages use this else use above

    # Convert to grayscale
    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding
    # thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)   #better for document scans

    # rotated = deskew(thresh)
    pdf_page = thresh
    return pdf_page












# if __name__ == "__main__":
#     output_folder = 'output'
#     pages = process_file(r'page_6.png',output_folder)
#     image = preprocess_image(pages)
#     import cv2
#     cv2.imwrite(f"haha/after.png",image)















