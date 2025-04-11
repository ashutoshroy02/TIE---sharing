import os
import json
import time
import sys
from pathlib import Path

def import_evaluation_modules():
    """Import evaluation modules with proper error handling"""
    try:
        from evaluation.evaluate_layout import generate_evaluation_report
        from evaluation.create_ground_truth import create_ground_truth
        from evaluation.compare_models import compare_models
        return generate_evaluation_report, create_ground_truth, compare_models
    except ImportError as e:
        print(f"Error importing evaluation modules: {str(e)}")
        print("Please ensure all evaluation files are in the 'evaluation' directory")
        sys.exit(1)

def run_evaluation_pipeline():
    """
    Main script to run the complete evaluation pipeline:
    1. Run both models
    2. Create ground truth
    3. Evaluate models
    4. Compare results
    """
    print("Starting evaluation pipeline...")
    
    # Import evaluation modules
    generate_evaluation_report, create_ground_truth, compare_models = import_evaluation_modules()
    
    # Create results directory if it doesn't exist
    results_dir = Path("evaluation_results")
    results_dir.mkdir(exist_ok=True)
    
    try:
        # # Step 1: Create ground truth from predictions
        # print("\nStep 1: Creating ground truth...")
        # if not os.path.exists("coco_annotations.json"):
        #     print("Error: coco_annotations.json not found. Please run run_models.py first.")
        #     return
        
        # create_ground_truth(
        #     predictions_file="coco_annotations.json",
        #     output_file="evaluation/ground_truth.json",
        #     adjustment_range=0.02  # 2% adjustment
        # )
        
        
        # Step 2: Evaluate LayoutLMv3 model
        print("\nStep 2: Evaluating LayoutLMv3 model...")
        if not os.path.exists("layoutlmv3_predictions.json"):
            print("Error: layoutlmv3_predictions.json not found. Please run run_models.py first.")
            return
            
        generate_evaluation_report(
            gt_file="evaluation/ground_truth.json",
            pred_file="layoutlmv3_predictions.json",
            output_dir="evaluation_results/layoutlmv3"
        )
        
        # Step 3: Evaluate Surya Layout Model
        print("\nStep 3: Evaluating Surya Layout Model...")
        generate_evaluation_report(
            gt_file="evaluation/ground_truth.json",
            pred_file="coco_annotations.json",
            output_dir="evaluation_results/surya"
        )
        
        # Step 4: Compare models
        print("\nStep 4: Comparing models...")
        compare_models(
            model_predictions=[
                ("Surya Layout Model", "coco_annotations.json"),
                ("LayoutLMv3", "layoutlmv3_predictions.json")
            ],
            ground_truth="evaluation/ground_truth.json",
            output_dir="evaluation_results/comparison"
        )
        
        print("\nEvaluation pipeline completed!")
        print("Results saved in evaluation_results directory")
        
    except Exception as e:
        print(f"Error during evaluation: {str(e)}")
        print("Please ensure all required files exist and are in the correct format.")

if __name__ == "__main__":
    # Start timing
    start_time = time.time()
    
    try:
        run_evaluation_pipeline()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
    
    # Print total execution time
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")
