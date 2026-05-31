import pytest
from unittest.mock import MagicMock
import io
from PIL import Image
from app.classifier import predict

def test_predict(mocker):
    mock_path = mocker.MagicMock()
    mock_path.exists.return_value = True
    mocker.patch("app.classifier.MODEL_PATH", mock_path)
    
    # Mock YOLO from ultralytics
    mock_yolo_class = mocker.patch("ultralytics.YOLO")
    mock_model_instance = MagicMock()
    mock_yolo_class.return_value = mock_model_instance
    
    # Set up the mock return value for model inference
    mock_result = MagicMock()
    mock_probs = MagicMock()
    mock_probs.top1 = 0
    mock_probs.top1conf = 0.95
    # Let's say we have 3 classes: 0: Alternaria Alternata, 1: Cercospora Nicotianae, 2: Healthy
    mock_probs.data.tolist.return_value = [0.95, 0.03, 0.02]
    mock_result.probs = mock_probs
    mock_model_instance.return_value = [mock_result]
    
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    result = predict(img_bytes)
    
    assert result["class_name"] == "Alternaria Alternata"
    assert result["confidence"] == 0.95
    assert len(result["top_predictions"]) == 3
    assert result["top_predictions"][0]["class_name"] == "Alternaria Alternata"
    assert result["top_predictions"][0]["confidence"] == 0.95
