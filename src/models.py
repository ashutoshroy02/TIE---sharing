''' Loads the models for the TIE project '''

from surya.layout import LayoutPredictor
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor

# Initialize Surya models globally  
layout_predictor = LayoutPredictor()
recognition_predictor = RecognitionPredictor()
detection_predictor = DetectionPredictor()      




