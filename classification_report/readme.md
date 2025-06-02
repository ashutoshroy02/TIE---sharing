# CLIP Image Classifier (Map, Photograph, Site Layout, Figure)

This Python script uses OpenAI's CLIP model to classify images into one of the following categories:

- **Map**
- **Photograph**
- **Site Layout**
- **Figure**

### 📊 Classification Report

| Class        | Precision | Recall | F1-Score | Support |
|--------------|-----------|--------|----------|---------|
| Figure       | 0.818     | 0.632  | 0.713    | 57      |
| Map          | 0.978     | 0.993  | 0.985    | 134     |
| Photograph   | 1.000     | 0.616  | 0.762    | 99      |
| Site Layout  | 0.692     | 1.000  | 0.818    | 110     |
| **Accuracy** |           |        | **0.850**| **—**   |

> **Overall Accuracy:** 85%
Tested the model on 400 images of four classes(map, photograph, site layout, figure) 

100 images from each classes downloaded from google [Archeological Maps, Archeological Photograph, Archeological Site Layout, Archeological Figures(Deawings)] 

![Confusion Matrix](sample_images/Figure_1.png)
---

## 📦 Features

- Classifies images using CLIP (ViT-B/32).
- Supports batch processing of multiple images and folders.
- Optionally computes accuracy, classification report, and confusion matrix.
- Saves classification metadata and evaluation metrics as JSON files.

---
Here are two sample images used for classification:

### 🖼️ Map Image (`1.png`)

![Map Image](sample_images/images35.jpg)

### 🗺️ Photograph Image (`2.png`)

![Photograph Image](sample_images/images118.jpg)

### 🖼️ Site layout Image (`1.png`)

![Site Layout Image](sample_images/images211.jpg)

### 🗺️ Figure Image (`2.png`)

![figure Image](sample_images/000009.jpg)


These images are used for testing the classifier and should be correctly identified as `map`, 'photograph', 'site layout' and 'figure'.


