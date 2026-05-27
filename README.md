# ChiGwarada 🍃 - Tobacco Leaf Disease Detection

An AI-powered web application for detecting diseases on tobacco leaves. It provides a bilingual (Shona/English) interface for diagnosing diseases either through image upload or voice/text symptom descriptions. 

This is a university final year AI and Machine Learning project.

## Features

- 📷 **Image Diagnosis**: Upload a picture of a tobacco leaf to get an instant diagnosis using a custom-trained YOLOv8 classification model.
- 💬 **Symptom Description**: Type or speak (using the browser's free Web Speech API) the symptoms to get an AI-powered diagnosis.
- 🌍 **Bilingual Interface**: Full support for English and Shona across the entire UI and AI-generated recommendations.
- 🎨 **Premium UI**: Modern dark-themed glassmorphism interface built with vanilla HTML/CSS/JS for high performance.
- 🛡️ **Anti-Abuse**: Built-in rate limiting and request tracking to protect the backend.

## Architecture

The project consists of three main parts:
1. **Machine Learning Pipeline**: A Google Colab notebook for training a YOLOv8 Nano classification model on a dataset of tobacco leaves.
2. **FastAPI Backend**: A Python backend that serves the frontend, runs local YOLOv8 inference (CPU-friendly), and communicates with OpenAI for bilingual farming recommendations.
3. **Frontend**: A sleek, responsive single-page web app.

## Setup Instructions

### Prerequisites
- Python 3.10+
- OpenAI API Key (for LLM recommendations)
- A trained `best.pt` YOLOv8 classification model

### 1. Model Training
1. Upload `notebooks/train_tobacco_model.py` to Google Colab and run it to train the model.
2. Download the resulting `best.pt` file.
3. Place `best.pt` in the `models/` directory of this project.

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
