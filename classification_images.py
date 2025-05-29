import os
import json
from datetime import datetime
from pathlib import Path
import clip
import torch
from PIL import Image
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

def setup_metadata_directory():
    # Create metadata directory in the same folder as the script
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    metadata_dir = script_dir / 'classification_metadata'
    metadata_dir.mkdir(exist_ok=True)
    return metadata_dir

def get_image_paths(paths):
    image_paths = []
    for path in paths:
        p = Path(path)
        if p.is_dir():
            image_paths.extend([str(f) for f in p.glob('*.jpg')] +
                               [str(f) for f in p.glob('*.jpeg')] +
                               [str(f) for f in p.glob('*.png')] +
                               [str(f) for f in p.glob('*.bmp')])
        elif p.is_file():
            image_paths.append(str(p))
    return image_paths

def calculate_accuracy(predictions, ground_truth, classes):
    """Calculate and print accuracy metrics"""
    y_true = ground_truth
    y_pred = predictions
    
    # Calculate overall accuracy
    accuracy = accuracy_score(y_true, y_pred)
    
    # Generate classification report
    report = classification_report(y_true, y_pred, target_names=classes)
    
    # Generate confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    
    print("\nAccuracy Metrics:")
    print(f"Overall Accuracy: {accuracy:.2%}")
    print("\nClassification Report:")
    print(report)
    # Print confusion matrix dynamically
    print("\nConfusion Matrix:")
    print("Predicted →")
    print("Actual ↓")
    
    # Print header row
    header = "          " + "  ".join([f"{c[:5]:<5s}" for c in classes])
    print(header)
    print("        " + "-" * len(header))
    
    # Print matrix rows
    for i, actual_class in enumerate(classes):
        row_prefix = f"{actual_class[:7]:<7s}  "
        row_data = "  ".join([f"{cm[i][j]:<5d}" for j in range(len(classes))])
        print(f"{row_prefix}{row_data}")
    
    return accuracy, report, cm

def classify_images(image_paths, model, preprocess, device, ground_truth=None):
    # Define classes and threshold
    classes = ['map', 'photograph', 'site layout', 'figure']
    results = {class_name: [] for class_name in classes}
    total_images = len(image_paths)
    
    # Lists to store predictions and ground truth for accuracy calculation
    all_predictions = []
    all_ground_truth = []
    
    for idx, image_path in enumerate(image_paths):
        try:
            # Print progress
            print(f"\rProcessing image {idx + 1}/{total_images}...", end="")
            
            image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
            text = clip.tokenize([f"a {c}" for c in classes]).to(device)
            with torch.no_grad():
                logits_per_image, _ = model(image, text)
                probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
                
                # Get index of the highest probability
                max_prob_index = np.argmax(probs)
                predicted_class = classes[max_prob_index]
                confidence = float(probs[max_prob_index])
                
                result = {
                    "filename": os.path.basename(image_path),
                    "predicted_label": predicted_class,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat()
                }
                results[predicted_class].append(result)
                
                # Store prediction for accuracy calculation
                all_predictions.append(predicted_class)
                if ground_truth:
                    all_ground_truth.append(ground_truth[idx])
                
                print(f"\n{result['filename']}: {predicted_class} (confidence: {result['confidence']:.2f})")
        except Exception as e:
            print(f"\nError processing {image_path}: {e}")
    
    print("\nClassification completed!")
    
    # Calculate accuracy if ground truth is provided
    if ground_truth:
        # Pass classes list to calculate_accuracy
        accuracy, report, cm = calculate_accuracy(all_predictions, all_ground_truth, classes)
        # Save accuracy metrics
        accuracy_metrics = {
            "accuracy": float(accuracy),
            "classification_report": report,
            "confusion_matrix": cm.tolist(),
            "timestamp": datetime.now().isoformat()
        }
        metadata_dir = setup_metadata_directory()
        with open(metadata_dir / "accuracy_metrics.json", "w") as f:
            json.dump(accuracy_metrics, f, indent=4)
    
    return results

def save_results(results, metadata_dir):
    for class_name, class_results in results.items():
        if not class_results:  # Skip if no images for this class
            continue
            
        output_file = metadata_dir / f"{class_name}_metadata.json"
        
        # Load existing results if file exists
        if output_file.exists():
            try:
                with open(output_file, "r") as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        else:
            existing = []
        
        # Append new results
        existing.extend(class_results)
        
        # Save updated results
        with open(output_file, "w") as f:
            json.dump(existing, f, indent=4)
        print(f"\nResults for {class_name} saved to {output_file}")

def main():
    print("CLIP Image Classifier (map, photograph, site layout, figure)")
    print("Note: Images will be classified based on the highest predicted probability among the four classes.")
    
    # Setup metadata directory
    metadata_dir = setup_metadata_directory()
    print(f"Metadata will be saved in: {metadata_dir}")
    
    # Get user input for images
    user_input = input("Enter image file(s) or folder(s), separated by commas: ").strip()
    if not user_input:
        print("No input provided. Exiting.")
        return
    
    # Process input paths
    user_paths = [p.strip() for p in user_input.split(",") if p.strip()]
    image_paths = get_image_paths(user_paths)
    if not image_paths:
        print("No images found.")
        return

    print(f"\nFound {len(image_paths)} images to process.")
    
    # Ask for ground truth labels if user wants to calculate accuracy
    calculate_accuracy_flag = input("\nDo you want to calculate accuracy? (yes/no): ").strip().lower() == 'yes'
    ground_truth = None
    
    if calculate_accuracy_flag:
        print("\nEnter ground truth labels for each image (map/image/layout/figure):")
        ground_truth = []
        valid_labels = ['map', 'photograph', 'site layout', 'figure']
        for image_path in image_paths:
            while True:
                label = input(f"Label for {os.path.basename(image_path)} ({'/'.join(valid_labels)}): ").strip().lower()
                if label in valid_labels:
                    ground_truth.append(label)
                    break
                print("Invalid label. Please enter one of the valid labels: map, image, layout, figure.")
    
    # Setup CLIP model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    model, preprocess = clip.load("ViT-B/32", device=device)

    # Classify images and save results
    results = classify_images(image_paths, model, preprocess, device, ground_truth)
    save_results(results, metadata_dir)

if __name__ == "__main__":
    main()
