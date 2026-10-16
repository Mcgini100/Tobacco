#  Agrivision - Tobacco Leaf Disease Detection

[![tests](https://github.com/Mcgini100/Tobacco/actions/workflows/tests.yml/badge.svg)](https://github.com/Mcgini100/Tobacco/actions/workflows/tests.yml)

An AI-powered web application for detecting diseases on tobacco leaves. It provides a bilingual (Shona/English) interface for diagnosing diseases either through image upload or voice/text symptom descriptions. 

Built for a client as a freelance project.

## Features

- **Image Diagnosis**: Upload a picture of a tobacco leaf to get an instant diagnosis using a custom-trained YOLOv8 classification model.
- **Symptom Description**: Type or speak (using the browser's free Web Speech API) the symptoms to get an AI-powered diagnosis.
- **Bilingual Interface**: Full support for English and Shona across the entire UI and AI-generated recommendations.
- **Premium UI**: Modern dark-themed glassmorphism interface built with vanilla HTML/CSS/JS for high performance.
- **Anti-Abuse**: Built-in rate limiting and request tracking to protect the backend.

## Architecture

The project consists of three main parts:
1. **Machine Learning Pipeline**: A Google Colab notebook for training a YOLOv8 Nano classification model on a dataset of tobacco leaves.
2. **FastAPI Backend**: A Python backend that serves the frontend, runs local YOLOv8 inference (CPU-friendly), and communicates with OpenAI for bilingual farming recommendations.
3. **Frontend**: A sleek, responsive single-page web app.

## Model evaluation (leak-free)

### Why the original 93.5% test accuracy was too optimistic

The Roboflow export has 1,268 images but only **73 distinct source photos**: each photo appears as several
transformed copies (mirrored, cropped, rotated), named `<photo>.rf.<hash>.jpg`. The export's own
train/valid/test split put copies of the same photo in more than one split (7 of the 22 test photos also had
copies in train), so the test set partly measured memorisation. A perceptual-hash check also found 5 pairs of
differently named sources that are the same photo.

### Method

1. `scripts/resplit_by_source.py` groups images by source photo (merging the 5 near-duplicate pairs: 68 groups),
   then splits **groups** 60/20/20 per class, so no photo has copies in two splits. The split is saved in
   [`data_splits/source_split.csv`](data_splits/source_split.csv) and checked by `tests/test_split.py`.
2. `scripts/train_clean_split.py` retrains `yolov8n-cls` with the same settings as
   `notebooks/train_tobacco_model.py` (imgsz 224, up to 50 epochs, patience 10, AdamW, same augmentation, seed 42).
   The checkpoint with the best validation accuracy (epoch 14) is kept.
3. `scripts/evaluate_clean_split.py` scores the held-out test photos.

| Split | Groups (photos) | Images |
|---|---|---|
| train | 42 | 805 |
| val | 13 | 193 |
| test | 13 | 270 |

### Results on the leak-free test split (13 photos, 270 images, never seen in training)

| Metric | Value |
|---|---|
| Accuracy (image level) | **76.7%** |
| Macro-F1 (image level) | **0.70** |
| Accuracy (photo level, probabilities averaged over a photo's copies) | 76.9% (10 / 13 photos) |

| Class | Precision | Recall | F1 | Test images |
|---|---|---|---|---|
| Alternaria alternata | 0.74 | 0.29 | 0.41 | 70 |
| Cercospora nicotianae | 0.77 | 0.92 | 0.84 | 148 |
| Healthy | 0.77 | 0.98 | 0.86 | 52 |

Confusion matrix (rows = true class, columns = predicted; order alternaria, cercospora, healthy):

```
[[ 20  41   9]
 [  6 136   6]
 [  1   0  51]]
```

Most errors are Alternaria leaves predicted as Cercospora: both are fungal leaf-spot diseases and the training
set has only 11 Alternaria photos.

### Which model the app ships

`models/best.pt` is still the model trained on the original Roboflow split. On the 6 clean-test photos
(40 images) that model never saw in training it classifies 39 of 40 images correctly, against 30 of 40 for the
retrained model, so the retrained weights were not swapped in. Six photos are far too few to measure the shipped
model's real accuracy; the leak-free numbers above are the honest estimate of what this training recipe achieves
on new photos. Full per-image results: [`data_splits/clean_split_results.json`](data_splits/clean_split_results.json).

### Dataset credit

[Tobacco leaf disease detection](https://universe.roboflow.com/kunyadini-oqbq0/tobacco-leaf-disease-detection-j3awg)
by a Roboflow Universe user, licensed **CC BY 4.0**. Classes: *Alternaria alternata*, *Cercospora nicotianae*,
and healthy leaves.

### Limitations

* Small dataset: 68 distinct photos across 3 classes, so every metric above has wide uncertainty
  (one photo is about 8% of the test set).
* Only three classes; other tobacco diseases, pests and nutrient deficiencies are not recognised and will be
  forced into one of the three labels.
* The photos' origin is not documented beyond Roboflow, and several file names point to public image libraries
  (e.g. Bugwood). Accuracy on farmers' own phone photos in the field has not been measured.
* The model is a decision aid; the LLM advice is generated text and should be checked with an extension officer.

## Setup Instructions

### Prerequisites
- Python 3.10+
- OpenAI API Key (for LLM recommendations)
- A trained `best.pt` YOLOv8 classification model

### 1. Model Training
1. Upload `notebooks/train_tobacco_model.py` to Google Colab and run it to train the model.
2. Download the resulting `best.pt` file.
3. Place `best.pt` in the `models/` directory of this project.

To reproduce the leak-free evaluation instead (CPU is fine, about 20 minutes):
```bash
python scripts/resplit_by_source.py --out dataset_clean
python scripts/train_clean_split.py --data dataset_clean
python scripts/evaluate_clean_split.py --weights models/best.pt runs/classify/tobacco_cls_clean_split/weights/best.pt
```

### 2. Backend Setup
1. Open a terminal in the project root directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your environment variables by editing `.env`:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   HF_ENDPOINT_URL=your_huggingface_endpoint_url_here
   HF_TOKEN=your_huggingface_api_key_here
   ```

### 3. Running the App
Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

The application will be available at [http://localhost:8000](http://localhost:8000).

## Deployment

For the final supervisor demo, you can run the app locally on your laptop:
1. Ensure the `best.pt` model is in the `models/` directory.
2. Start the Uvicorn server.
3. Open `http://localhost:8000` in your web browser.

Alternatively, you can deploy the app to a free tier hosting service like Render or Railway. Make sure to set the `OPENAI_API_KEY` in the hosting environment variables.
