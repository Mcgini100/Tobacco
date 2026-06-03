# Assessor Q&A and Core Implementations
> [!NOTE]
> This document outlines potential questions an assessor might ask during a project review, along with detailed responses and code snippets highlighting the core functionality of the Tobacco Leaf Disease Detection application.

## Potential Assessor Questions & Responses

**Q1: What specific problem does this application solve, and who is the target audience?**
**Response:** This application helps smallholder tobacco farmers in Zimbabwe accurately diagnose common tobacco leaf diseases, such as *Alternaria Alternata* (Brown Spot) and *Cercospora Nicotianae* (Frog Eye). It bridges the gap in agronomic expertise by offering an accessible, bilingual (English and Shona) diagnosis tool that provides practical farming recommendations based on uploaded images, text descriptions, or voice recordings.

**Q2: How does the application handle image classification, and why did you choose this approach?**
**Response:** Image classification is handled by a custom-trained YOLOv8 nano classification model (`yolov8n-cls`). This architecture was chosen because it strikes an excellent balance between inference speed and accuracy, making it lightweight enough to run without requiring a heavy GPU in production. The model takes a preprocessed 640x640 image and outputs confidence scores across three classes: Alternaria Alternata, Cercospora Nicotianae, and Healthy.

**Q3: How do you handle edge cases, such as users uploading non-plant images or images where the model is uncertain?**
**Response:** If the YOLO model's confidence falls below 60%, the backend triggers a fallback mechanism instructing the LLM to give a cautious diagnosis and advise the user to capture a clearer picture. Additionally, we implemented a secondary `check_for_new_diseases_vision` function using GPT-4o-mini's vision capabilities. This acts as a safeguard to reject images that are "Not a Plant" and can detect other diseases (like TMV or Angular Leaf Spot) that the base YOLO model was not explicitly trained on.

**Q4: How is Large Language Model (LLM) technology integrated into the system?**
**Response:** We use OpenAI's `gpt-4o-mini` to translate the raw classification results into farmer-friendly, actionable advice in both English and Shona. The LLM handles the generation of disease descriptions and practical recommendations (cultural and chemical controls). It can be triggered via the image pipeline (translating YOLO predictions) or via the description pipeline (interpreting free-text or transcribed voice symptoms).

**Q5: Describe your model training process (referencing `tune_tobacco.ipynb`).**
**Response:** The model was fine-tuned using a structured Colab pipeline (documented in `notebooks/train_tobacco_model.py` and `Tune_tobacco.ipynb`). Specifically, **fine-tuning** was done by taking a pre-trained `yolov8n-cls` base model (which already understands general image features from a massive dataset) and training it further exclusively on our custom Roboflow tobacco leaf dataset. We applied data augmentations (HSV, rotation, translation, scaling, flips) to prevent overfitting, fine-tuned the model for 50 epochs, and exported the `best.pt` weights for production use.

---

## Core Functions & Code Implementations

Below are the core pillars of the application's implementation.

### 1. YOLOv8 Classification Interface
The `predict` function is responsible for preparing the image and running it through the pre-trained model.

```python
# From app/classifier.py
def predict(image_bytes: bytes) -> dict[str, Any]:
    model = _load_model() # Lazy-loaded singleton

    # Decode & Enhance image
    from PIL import ImageOps
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = ImageOps.exif_transpose(image)
    image = image.resize((640, 640), Image.Resampling.BILINEAR)

    # Run inference
    results = model(image, verbose=False)
    probs = results[0].probs

    # Extract Top-1 prediction
    top_idx = int(probs.top1)
    top_conf = float(probs.top1conf)
    class_name = CLASS_MAP.get(top_idx, f"Unknown ({top_idx})")

    return {
        "class_name": class_name,
        "confidence": round(top_conf, 4),
        "top_predictions": [...] # Parsed ranked list
    }
```

### 2. Main API Endpoint (`/api/diagnose`)
This FastAPI endpoint orchestrates the pipeline: receiving the file upload, running the YOLO classifier, running the vision fallback, and generating the final LLM diagnosis.

```python
# From app/main.py
@app.post("/api/diagnose")
async def diagnose_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
) -> dict[str, Any]:
    
    image_bytes = await file.read()

    # Step 1: Classify with YOLO
    prediction = predict(image_bytes)
    
    # Step 2: Smoke and mirrors for new diseases / Reject non-plants
    vision_override = await check_for_new_diseases_vision(image_bytes, prediction["class_name"])
    if vision_override == "Not a Plant":
        raise HTTPException(status_code=400, detail="The uploaded image does not appear to be a plant.")
        
    if vision_override and vision_override != "None":
        prediction["class_name"] = vision_override
        prediction["confidence"] = 0.95

    # Step 3: LLM diagnosis generation
    diagnosis = await get_diagnosis_from_image(
        class_name=prediction["class_name"],
        confidence=prediction["confidence"],
    )

    return {
        "success": True,
        "prediction": prediction,
        "diagnosis": diagnosis,
    }
```

### 3. LLM Bilingual Integration
The LLM service generates contextual advice tailored for Zimbabwean smallholder farmers. Notice how low-confidence inputs are handled gracefully.

```python
# From app/llm_service.py
async def get_diagnosis_from_image(class_name: str, confidence: float) -> dict[str, Any]:
    if confidence < 0.60:
        user_prompt = (
            f"The AI classifier indicated a low-confidence match ({confidence:.1%} confidence) "
            f"for **{class_name}**. DO NOT give a definitive diagnosis. Instead, provide a cautious description "
            "in English and Shona... and a STRONG disclaimer advising the farmer to take a clearer photo."
        )
    else:
        user_prompt = (
            f"The AI classifier detected **{class_name}** with {confidence:.1%} confidence.\n\n"
            "Provide a brief description, practical farming recommendations, and a note about confidence "
            "in both English and Shona."
        )

    return await _call_llm(user_prompt)
```

### 4. Model Training Pipeline (`Tune_tobacco.ipynb`)
The base model is fine-tuned using `ultralytics` on the gathered dataset, incorporating robustness through data augmentation.

```python
# From notebooks/train_tobacco_model.py & Tune_tobacco.ipynb
from ultralytics import YOLO

# 1. Load base nano classification model (This is the starting point for fine-tuning)
model = YOLO('yolov8n-cls.pt')

# 2. Train configuration (This is where the actual fine-tuning on our custom dataset happens)
results = model.train(
    data='dataset_yolo',           # The custom tobacco dataset
    epochs=50,                     # Fine-tuning for 50 epochs
    imgsz=224,                     
    batch=32,                      
    patience=10,                   
    optimizer='AdamW',             
    lr0=0.001,                     
    augment=True,                  
    hsv_h=0.015, hsv_s=0.7, hsv_v=0.4, # Augmentations
    degrees=15.0, translate=0.1, scale=0.5,
    fliplr=0.5,                    
    name='tobacco_disease_cls',    
    project='runs/classify',       
)
```
