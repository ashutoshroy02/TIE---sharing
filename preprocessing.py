'''This code preprocess the page. 1. grayscale  2. denoise   3.thresh . overall it black and white the page .
Also removes the unwanted color. Enhances the text with 200 dpi . removes unawanted borders . 
Does not work for Shadow pages. if the page has a little shadow it darkens it very much'''

import cv2
import numpy as np
from pdf_to_pages import process_file

# def deskew(image):
    #         co_ords = np.column_stack(np.where(image > 0))
    #         angle = cv2.minAreaRect(co_ords)[-1]
    #         if angle < -45:
    #             angle   = -(90 + angle)
    #         else:
    #             angle = -angle
    #             (h, w) = image.shape[:2]
    #             center = (w // 2, h // 2)
    #         M = cv2.getRotationMatrix2D(center, angle, 1.0)
    #         rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC,
    #         borderMode=cv2.BORDER_REPLICATE)
    #         return rotated
    

import cv2
import numpy as np


def preprocess_image(image):

    # Convert PIL Image to OpenCV format
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
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


file_path = r'book2-120-125.pdf' 
pages = process_file(file_path)
preprocessed_pages = [preprocess_image(page) for page in pages]





"""# Display the original pages
from PIL import Image
for idx, page in enumerate(pages):
    print(f"Displaying page {idx+1}")
    page.show()
    input("Press Enter to continue to the next page...")"""


"""# Display the preprocessed pages
for idx, preprocessed_page in enumerate(preprocessed_pages):
    print(f"Displaying preprocessed page {idx+1}")
    # Convert OpenCV image (numpy array) back to PIL Image for display
    pil_img = Image.fromarray(preprocessed_page)
    pil_img.show()
    input("Press Enter to continue to the next preprocessed page...")
"""


##to test
'''##with pdf as file
# Load the pages from the PDF
# file_path = r'book2-120-125.pdf' 
# preprocessed_pages = [preprocess_image(page) for page in pages]
# for idx, img in enumerate(preprocessed_pages):
    # pil_img = Image.fromarray(img)
    # pil_img.show(title=f"Page {idx+1}")
    # input() '''


'''##with image as file
# file_path = r"Z:\TO DO\codes\IIT\ashu\model_output\original dataset\heading and two cloumn.png"
#from PIL import Image
# img = cv2.cvtColor(np.array(file_path), cv2.COLOR_RGB2BGR)
# Image.fromarray(img).show()
'''

'''##with folder of images to test
import os
current_path = os.getcwd()
folder_path = os.path.join(current_path, 'model_output', 'original dataset')
files_path = [os.path.join(folder_path, file) for file in os.listdir(folder_path)]

all_pages = []
for i in files_path:
    pages = process_file(i)
    all_pages.extend(pages)

preprocessed_pages = [preprocess_image(i) for i in all_pages]

#display image
from PIL import Image
for idx, img in enumerate(preprocessed_pages):
    pil_img = Image.fromarray(img)
    pil_img.show(title=f"Page {idx+1}")
    input("enter for next page)
'''


#SAVE IN A FOLDER
'''import os
from PIL import Image
current_path = os.getcwd()
folder_path = os.path.join(current_path, 'model_output', 'original dataset')
files_path = [os.path.join(folder_path, file) for file in os.listdir(folder_path)]

all_pages = []
for i in files_path:
    pages = process_file(i)
    all_pages.extend(pages)

preprocessed_pages = [preprocess_image(i) for i in all_pages]

if not os.path.exists(os.path.join(current_path,'model_output', 'after_preprocessing')):
     os.makedirs(os.path.join(current_path,'model_output', 'after_preprocessing'))

for i, img in enumerate(preprocessed_pages):
    if isinstance(img, np.ndarray):
        img = Image.fromarray(img)
    img_path =os.path.join(current_path,'model_output', 'after_preprocessing', f"page_{i+1}.png")
    img.save(img_path)
    print(f"Saved: {img_path}")'''