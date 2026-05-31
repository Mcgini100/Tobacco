import pytest
import io
from PIL import Image

def test_health_check(client, mocker):
    # We don't necessarily need to mock BASE_DIR logic if we just want to ensure it doesn't crash,
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_register(client):
    response = client.post("/api/register", json={"username": "testuser123", "password": "password123"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Try duplicate
    response_duplicate = client.post("/api/register", json={"username": "testuser123", "password": "password123"})
    assert response_duplicate.status_code == 400

def test_login(client):
    client.post("/api/register", json={"username": "logintester", "password": "password123"})
    
    response = client.post("/api/login", data={"username": "logintester", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # Wrong password
    response_wrong = client.post("/api/login", data={"username": "logintester", "password": "wrongpassword"})
    assert response_wrong.status_code == 401

def test_diagnose_image(client, mocker):
    # Setup user
    client.post("/api/register", json={"username": "diagtester", "password": "password123"})
    login_res = client.post("/api/login", data={"username": "diagtester", "password": "password123"})
    token = login_res.json()["access_token"]
    
    mocker.patch("app.main.predict", return_value={
        "class_name": "Alternaria Alternata", 
        "confidence": 0.95, 
        "top_predictions": []
    })
    mock_llm = mocker.patch("app.main.get_diagnosis_from_image", new_callable=mocker.AsyncMock)
    mock_llm.return_value = {"disease_name_en": "Alternaria Alternata"}
    
    img = Image.new('RGB', (10, 10), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    response = client.post(
        "/api/diagnose",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["prediction"]["class_name"] == "Alternaria Alternata"

def test_describe_symptoms(client, mocker):
    # Setup user
    client.post("/api/register", json={"username": "desctester", "password": "password123"})
    login_res = client.post("/api/login", data={"username": "desctester", "password": "password123"})
    token = login_res.json()["access_token"]
    
    mock_llm = mocker.patch("app.main.get_diagnosis_from_description", new_callable=mocker.AsyncMock)
    mock_llm.return_value = {"disease_name_en": "Healthy"}
    
    response = client.post(
        "/api/describe",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "Leaves look perfectly green and fine.", "language": "en"}
    )
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["diagnosis"]["disease_name_en"] == "Healthy"
