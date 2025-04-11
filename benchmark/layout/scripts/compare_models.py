import json
import os
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def evaluate_model(gt_file, pred_file, model_name):
    """
    Evaluate a single model's performance.
    """
    # Load ground truth
    coco_gt = COCO(gt_file)
    
    # Load predictions
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
    
    # Initialize COCO evaluation
    coco_eval = COCOeval(coco_gt, coco_dt, 'bbox')
    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()
    
    return {
        'model_name': model_name,
        'AP': float(coco_eval.stats[0]),
        'AP50': float(coco_eval.stats[1]),
        'AP75': float(coco_eval.stats[2]),
        'AR': float(coco_eval.stats[8])
    }

def compare_models(gt_file, model_predictions):
    """
    Compare multiple models' performance.
    
    Args:
        gt_file: Path to ground truth COCO annotations
        model_predictions: List of tuples (model_name, prediction_file)
    """
    results = []
    
    # Evaluate each model
    for model_name, pred_file in model_predictions:
        print(f"\nEvaluating {model_name}...")
        results.append(evaluate_model(gt_file, pred_file, model_name))
    
    # Print comparison table
    print("\nModel Comparison:")
    print(f"{'Model':<20} {'AP':<10} {'AP50':<10} {'AP75':<10} {'AR':<10}")
    print("-" * 60)
    for result in results:
        print(f"{result['model_name']:<20} {result['AP']:.3f}     {result['AP50']:.3f}     {result['AP75']:.3f}     {result['AR']:.3f}")
    
    # Create visualization
    plt.figure(figsize=(12, 6))
    
    # AP comparison
    plt.subplot(1, 2, 1)
    models = [r['model_name'] for r in results]
    aps = [r['AP'] for r in results]
    plt.bar(models, aps)
    plt.title('Average Precision (AP) Comparison')
    plt.xticks(rotation=45)
    plt.ylim(0, 1)
    
    # AR comparison
    plt.subplot(1, 2, 2)
    ars = [r['AR'] for r in results]
    plt.bar(models, ars)
    plt.title('Average Recall (AR) Comparison')
    plt.xticks(rotation=45)
    plt.ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig('evaluation/model_comparison.png')
    # print("\nComparison visualization saved as 'model_comparison.png'")
    
    return results

if __name__ == "__main__":
    # Path to ground truth
    gt_file = "evaluation\ground_truth.json"
    
    # List of models to compare
    model_predictions = [
        ("Surya Layout Model", "evaluation\coco_annotations.json"),
        ("LayoutLMv3", "evaluation\layoutlmv3_predictions.json")
    ]
    
    # Run comparison
    results = compare_models(gt_file, model_predictions)
    
    # Save results
    with open('model_comparison_results.json', 'w') as f:
        json.dump(results, f, indent=2) 