import cv2
import numpy as np
import easyocr
import tempfile
import os
import requests
import json

class OCRProcessor:
    """Processes different types of content with appropriate OCR models."""
    
    def __init__(self):
        """Initialize OCR models."""
        # Initialize EasyOCR reader
        self.reader = easyocr.Reader(['en'])
    
    def process(self, image, content_type="text"):
        """
        Process an image with appropriate OCR model based on content type.
        
        Args:
            image: Input image (numpy array)
            content_type: Type of content ("text", "table", "image", etc.)
            
        Returns:
            Extracted content as string or structured data
        """
        if content_type == "text":
            return self._process_text(image)
        elif content_type == "table":
            return self._process_table(image)
        elif content_type in ["image", "figure"]:
            return self._process_image(image)
        else:
            # Default to text processing
            return self._process_text(image)
    
    def _process_text(self, image):
        """Process text content with OCR."""
        # Use EasyOCR for text extraction
        results = self.reader.readtext(image)
        
        # Combine all detected text blocks
        text_blocks = []
        for detection in results:
            text = detection[1]  # detection format: ([[x1,y1], [x2,y2], [x3,y3], [x4,y4]], text, confidence)
            text_blocks.append(text)
        
        return '\n'.join(text_blocks)
    
    def _process_table(self, image):
        """Process table content with specialized OCR."""
        # For tables, we'll use EasyOCR to detect all text and then try to structure it
        results = self.reader.readtext(image)
        
        # Sort results by vertical position (y-coordinate) to group rows
        sorted_results = sorted(results, key=lambda x: (x[0][0][1] + x[0][2][1]) / 2)  # Average y-coordinate
        
        # Group text by rows based on y-coordinate proximity
        rows = []
        current_row = []
        last_y = None
        y_threshold = 20  # Adjust this value based on your needs
        
        for detection in sorted_results:
            bbox, text, conf = detection
            current_y = (bbox[0][1] + bbox[2][1]) / 2
            
            if last_y is None or abs(current_y - last_y) <= y_threshold:
                current_row.append(text)
            else:
                if current_row:
                    rows.append(current_row)
                current_row = [text]
            
            last_y = current_y
        
        if current_row:
            rows.append(current_row)
        
        # Convert to markdown table format
        if not rows:
            return ""
        
        # Create markdown table
        markdown_rows = []
        
        # Header
        if rows:
            header = " | ".join(rows[0])
            markdown_rows.append(f"| {header} |")
            separator = " | ".join(["---"] * len(rows[0]))
            markdown_rows.append(f"| {separator} |")
        
        # Data rows
        for row in rows[1:]:
            # Pad row if necessary
            while len(row) < len(rows[0]):
                row.append("")
            data_row = " | ".join(row)
            markdown_rows.append(f"| {data_row} |")
        
        return "\n".join(markdown_rows)
    
    def _process_image(self, image):
        """Process image/figure content."""
        # For images, we might extract caption text or just identify it as an image
        # Try to find any caption text using OCR
        results = self.reader.readtext(image)
        if results:
            caption = " ".join([detection[1] for detection in results])
            return f"[Image with caption: {caption}]"
        return "[Image content]"


class TextCorrector:
    """Handles text from OCR without grammar correction."""
    
    def __init__(self, api_key=None, model="mixtral-8x7b-32768"):
        """
        Initialize text corrector.
        
        Args:
            api_key: API key for Groq service
            model: Model to use (default: mixtral-8x7b-32768)
        """
        self.api_key = "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"
        self.model = model
        if self.api_key:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
    
    def correct(self, text):
        """
        Process the OCR text without grammar correction.
        
        Args:
            text: Input text from OCR
            
        Returns:
            Processed text
        """
        if not text or len(text.strip()) < 10:
            return text
            
        if self.api_key:
            return self._process_with_groq(text)
        else:
            return self._simple_process(text)
    
    def _process_with_groq(self, text):
        """Use Groq API to process text."""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that processes OCR text. Do not correct grammar or spelling - just return the text as is, only fixing obvious OCR errors like character substitutions (e.g. '0' instead of 'O') or merging split words."},
                    {"role": "user", "content": f"Process this OCR text, keeping original grammar and spelling:\n\n{text}"}
                ],
                temperature=0.1
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Error using Groq API for text processing: {e}")
            return text
    
    def _simple_process(self, text):
        """
        Simple text processing without using an LLM.
        Just returns the original text.
        """
        return text
