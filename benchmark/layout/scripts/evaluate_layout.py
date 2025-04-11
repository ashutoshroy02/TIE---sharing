import json
import os
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def load_coco_annotations(annotation_file):
    """
    Load COCO annotations from file.
    
    Args:
        annotation_file: Path to the COCO annotation file
        
    Returns:
        COCO object containing the annotations
    """
    if not os.path.exists(annotation_file):
        raise FileNotFoundError(f"Annotation file not found: {annotation_file}")
    
    return COCO(annotation_file)

def evaluate_model(gt_file, pred_file):
    """
    Evaluate model performance using COCO metrics.
    
    Args:
        gt_file: Path to ground truth COCO annotations
        pred_file: Path to model predictions in COCO format
    """
    # Load ground truth
    coco_gt = load_coco_annotations(gt_file)
    
    # Load predictions
    with open(pred_file, 'r') as f:
        predictions = json.load(f)
    
    # Convert predictions to COCO format
    if isinstance(predictions, dict) and 'annotations' in predictions:
        predictions = predictions['annotations']
    
    # Add score field to predictions (required by COCO)
    for pred in predictions:
        if 'confidence' in pred:
            pred['score'] = pred['confidence']
        else:
            pred['score'] = 1.0  # Default score if confidence not available
    
    coco_dt = coco_gt.loadRes(predictions)
    
    # Initialize COCO evaluation
    coco_eval = COCOeval(coco_gt, coco_dt, 'bbox')
    
    # Run evaluation
    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()
    
    # Print detailed metrics
    print("\nDetailed Metrics:")
    print(f"Average Precision (AP) @[ IoU=0.50:0.95 | area=   all | maxDets=100 ] = {coco_eval.stats[0]:.3f}")
    print(f"Average Precision (AP) @[ IoU=0.50      | area=   all | maxDets=100 ] = {coco_eval.stats[1]:.3f}")
    print(f"Average Precision (AP) @[ IoU=0.75      | area=   all | maxDets=100 ] = {coco_eval.stats[2]:.3f}")
    print(f"Average Precision (AP) @[ IoU=0.50:0.95 | area= small | maxDets=100 ] = {coco_eval.stats[3]:.3f}")
    print(f"Average Precision (AP) @[ IoU=0.50:0.95 | area=medium | maxDets=100 ] = {coco_eval.stats[4]:.3f}")
    print(f"Average Precision (AP) @[ IoU=0.50:0.95 | area= large | maxDets=100 ] = {coco_eval.stats[5]:.3f}")
    print(f"Average Recall    (AR) @[ IoU=0.50:0.95 | area=   all | maxDets=  1 ] = {coco_eval.stats[6]:.3f}")
    print(f"Average Recall    (AR) @[ IoU=0.50:0.95 | area=   all | maxDets= 10 ] = {coco_eval.stats[7]:.3f}")
    print(f"Average Recall    (AR) @[ IoU=0.50:0.95 | area=   all | maxDets=100 ] = {coco_eval.stats[8]:.3f}")
    
    return coco_eval

def analyze_category_performance(coco_gt, coco_dt):
    """
    Analyze model performance per category.
    
    Args:
        coco_gt: COCO object containing ground truth
        coco_dt: COCO object containing predictions
    """
    # Get category names
    cats = coco_gt.loadCats(coco_gt.getCatIds())
    cat_names = [cat['name'] for cat in cats]
    
    # Initialize evaluation for each category
    category_stats = defaultdict(dict)
    
    for cat_id, cat_name in zip(coco_gt.getCatIds(), cat_names):
        # Create evaluation object for this category
        coco_eval = COCOeval(coco_gt, coco_dt, 'bbox')
        coco_eval.params.catIds = [cat_id]
        
        # Run evaluation
        coco_eval.evaluate()
        coco_eval.accumulate()
        coco_eval.summarize()
        
        # Store results, replace -1 with 0 for better readability
        stats = {
            'AP': max(0, coco_eval.stats[0]),
            'AP50': max(0, coco_eval.stats[1]),
            'AP75': max(0, coco_eval.stats[2]),
            'AR': max(0, coco_eval.stats[8])
        }
        
        # Only add categories that have detections
        if any(v > 0 for v in stats.values()):
            category_stats[cat_name] = stats
    
    # Print category-wise results
    print("\nCategory-wise Performance:")
    print(f"{'Category':<20} {'AP':<10} {'AP50':<10} {'AP75':<10} {'AR':<10}")
    print("-" * 60)
    for cat_name, stats in category_stats.items():
        print(f"{cat_name:<20} {stats['AP']:.3f}     {stats['AP50']:.3f}     {stats['AP75']:.3f}     {stats['AR']:.3f}")

def visualize_predictions(image_path, coco_file, output_path=None):
    """
    Visualize predictions on an image.
    
    Args:
        image_path: Path to the image
        coco_file: Path to the COCO annotation file
        output_path: Optional path to save the visualization
    """
    # Load COCO annotations
    coco = load_coco_annotations(coco_file)
    
    # Load image
    img = plt.imread(image_path)
    plt.figure(figsize=(15, 10))
    plt.imshow(img)
    
    # Get annotations for this image
    img_id = coco.getImgIds(imgIds=[os.path.basename(image_path)])[0]
    ann_ids = coco.getAnnIds(imgIds=img_id)
    anns = coco.loadAnns(ann_ids)
    
    # Draw bounding boxes
    coco.showAnns(anns)
    
    if output_path:
        plt.savefig(output_path)
        print(f"Visualization saved to {output_path}")
    else:
        plt.show()

def generate_evaluation_report(gt_file, pred_file, output_dir='evaluation_results'):
    """
    Generate a comprehensive evaluation report.
    
    Args:
        gt_file: Path to ground truth COCO annotations
        pred_file: Path to model predictions in COCO format
        output_dir: Directory to save evaluation results
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load annotations
    coco_gt = load_coco_annotations(gt_file)
    with open(pred_file, 'r') as f:
        predictions = json.load(f)
    
    # Convert predictions to COCO format
    if isinstance(predictions, dict) and 'annotations' in predictions:
        predictions = predictions['annotations']
    
    # Add score field to predictions
    for pred in predictions:
        if 'confidence' in pred:
            pred['score'] = pred['confidence']
        else:
            pred['score'] = 1.0
    
    coco_dt = coco_gt.loadRes(predictions)
    
    # Run evaluation
    coco_eval = evaluate_model(gt_file, pred_file)
    
    # Analyze category performance
    analyze_category_performance(coco_gt, coco_dt)
    
    # Save evaluation results
    results = {
        'overall_metrics': {
            'AP': float(coco_eval.stats[0]),
            'AP50': float(coco_eval.stats[1]),
            'AP75': float(coco_eval.stats[2]),
            'AR': float(coco_eval.stats[8])
        },
        'category_metrics': {}
    }
    
    # Get category-wise metrics
    for cat_id in coco_gt.getCatIds():
        cat = coco_gt.loadCats(cat_id)[0]
        coco_eval = COCOeval(coco_gt, coco_dt, 'bbox')
        coco_eval.params.catIds = [cat_id]
        coco_eval.evaluate()
        coco_eval.accumulate()
        coco_eval.summarize()
        
        results['category_metrics'][cat['name']] = {
            'AP': float(coco_eval.stats[0]),
            'AP50': float(coco_eval.stats[1]),
            'AP75': float(coco_eval.stats[2]),
            'AR': float(coco_eval.stats[8])
        }
    
    # Save results to file
    with open(os.path.join(output_dir, 'evaluation_results.json'), 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nEvaluation report saved to {os.path.join(output_dir, 'evaluation_results.json')}")

# Example usage
if __name__ == "__main__":
    # Paths to annotation files
    gt_file = "ground_truth.json"
    pred_file = "coco_annotations.json"
    
    # Generate evaluation report
    generate_evaluation_report(gt_file, pred_file)
    
    # Example image path - replace with actual image path
    image_path = r"Z:\TO DO\codes\IIT\ashu\model_output\original dataset\two column and table.png"
    if os.path.exists(image_path):
        visualize_predictions(image_path, pred_file, "visualization.png")
    else:
        print(f"Image not found: {image_path}") 