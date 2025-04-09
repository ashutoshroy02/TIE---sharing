import pytesseract
import easyocr
import cv2
import numpy as np
from typing import List, Tuple, Dict
import Levenshtein
from dataclasses import dataclass
from transformers import AutoTokenizer, AutoModelForSeq2SeqGeneration
import torch

@dataclass
class OCRResult:
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]

class TextRecognizer:
    """Advanced text recognition system combining multiple OCR engines."""
    
    def __init__(self, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.device = device
        
        # Initialize OCR engines
        self.reader = easyocr.Reader(['en'])
        
        # Initialize text correction model
        self.tokenizer = AutoTokenizer.from_pretrained('facebook/bart-large')
        self.correction_model = AutoModelForSeq2SeqGeneration.from_pretrained('facebook/bart-large')
        self.correction_model.to(device)
        
        # Configure Tesseract
        self.tesseract_config = '--oem 1 --psm 6'
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: Input image
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Adaptive thresholding
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Dilation to connect text components
        kernel = np.ones((1, 1), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=1)
        
        return dilated
    
    def recognize_text(self, image: np.ndarray, region_type: str = "Text") -> List[OCRResult]:
        """
        Recognize text in the image using multiple OCR engines.
        
        Args:
            image: Input image
            region_type: Type of the text region (affects processing)
            
        Returns:
            List of OCR results with text and confidence scores
        """
        # Preprocess image
        processed_img = self.preprocess_image(image)
        
        # Get results from both engines
        easy_results = self.reader.readtext(processed_img)
        tesseract_results = self._get_tesseract_results(processed_img)
        
        # Combine and deduplicate results
        combined_results = []
        
        # Process EasyOCR results
        for bbox, text, conf in easy_results:
            x1, y1 = map(int, bbox[0])
            x2, y2 = map(int, bbox[2])
            combined_results.append(OCRResult(
                text=text,
                confidence=conf,
                bbox=(x1, y1, x2, y2)
            ))
        
        # Process Tesseract results
        for result in tesseract_results:
            # Check for duplicates using bbox overlap and text similarity
            is_duplicate = False
            for existing in combined_results:
                if self._is_duplicate(result, existing):
                    # Keep the one with higher confidence
                    if result.confidence > existing.confidence:
                        combined_results.remove(existing)
                        combined_results.append(result)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                combined_results.append(result)
        
        # Sort by vertical position
        combined_results.sort(key=lambda x: x.bbox[1])
        
        return combined_results
    
    def _get_tesseract_results(self, image: np.ndarray) -> List[OCRResult]:
        """Get OCR results from Tesseract."""
        results = []
        
        # Get detailed OCR data
        data = pytesseract.image_to_data(image, config=self.tesseract_config, output_type=pytesseract.Output.DICT)
        
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            if int(data['conf'][i]) > 0:  # Filter out low confidence results
                x, y, w, h = (
                    data['left'][i],
                    data['top'][i],
                    data['width'][i],
                    data['height'][i]
                )
                
                results.append(OCRResult(
                    text=data['text'][i],
                    confidence=float(data['conf'][i]) / 100,
                    bbox=(x, y, x + w, y + h)
                ))
        
        return results
    
    def _is_duplicate(self, result1: OCRResult, result2: OCRResult, 
                     iou_threshold: float = 0.5, text_similarity_threshold: float = 0.8) -> bool:
        """Check if two OCR results are duplicates."""
        # Check bbox overlap using IoU
        bbox1 = result1.bbox
        bbox2 = result2.bbox
        
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 < x1 or y2 < y1:
            return False
            
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        iou = intersection / float(area1 + area2 - intersection)
        
        if iou < iou_threshold:
            return False
            
        # Check text similarity using Levenshtein distance
        similarity = 1 - Levenshtein.distance(result1.text, result2.text) / max(len(result1.text), len(result2.text))
        
        return similarity >= text_similarity_threshold
    
    def post_process_text(self, text: str, context: str = "") -> str:
        """
        Post-process recognized text using the correction model.
        
        Args:
            text: Text to process
            context: Optional context to help with correction
            
        Returns:
            Processed text
        """
        if not text.strip():
            return text
            
        # Prepare input for the model
        if context:
            input_text = f"Context: {context}\nText: {text}"
        else:
            input_text = text
            
        # Tokenize
        inputs = self.tokenizer(input_text, return_tensors='pt', max_length=512, truncation=True)
        inputs = inputs.to(self.device)
        
        # Generate correction
        with torch.no_grad():
            outputs = self.correction_model.generate(
                **inputs,
                max_length=512,
                num_beams=4,
                length_penalty=2.0,
                early_stopping=True
            )
            
        corrected_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return corrected_text 