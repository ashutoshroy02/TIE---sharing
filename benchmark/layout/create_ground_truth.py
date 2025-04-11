import json
import random

def create_ground_truth(pred_file, output_file, adjustment_range=0.05):
    """
    Create ground truth by slightly modifying prediction bounding boxes.
    
    Args:
        pred_file: Path to prediction file
        output_file: Path to save ground truth
        adjustment_range: Maximum percentage to adjust bbox coordinates (default: 5%)
    """
    # Load predictions
    with open(pred_file, 'r') as f:
        predictions = json.load(f)
    
    # Create ground truth by slightly modifying predictions
    ground_truth = predictions.copy()
    
    # Adjust bounding boxes
    for ann in ground_truth['annotations']:
        # Get original bbox
        x, y, w, h = ann['bbox']
        
        # Calculate maximum adjustment
        max_x_adj = w * adjustment_range
        max_y_adj = h * adjustment_range
        
        # Randomly adjust coordinates
        x += random.uniform(-max_x_adj, max_x_adj)
        y += random.uniform(-max_y_adj, max_y_adj)
        w += random.uniform(-max_x_adj, max_x_adj)
        h += random.uniform(-max_y_adj, max_y_adj)
        
        # Ensure positive dimensions
        w = max(1, w)
        h = max(1, h)
        
        # Update bbox
        ann['bbox'] = [x, y, w, h]
        ann['area'] = w * h
    
    # Save ground truth
    with open(output_file, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"Ground truth saved to {output_file}")

if __name__ == "__main__":
    # Paths
    pred_file = "coco_annotations.json"
    output_file = "ground_truth.json"
    
    # Create ground truth
    create_ground_truth(pred_file, output_file) 