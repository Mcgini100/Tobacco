import pytest
from app.database import (
    create_user,
    authenticate_user,
    verify_password,
    get_password_hash,
    create_access_token
)
from jose import jwt
from app.database import SECRET_KEY, ALGORITHM

def test_password_hashing():
    password = "supersecretpassword"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_create_user():
    success = create_user("testuser", "testpass")
    assert success is True
    
    # Try to create the same user again
    success_duplicate = create_user("testuser", "testpass2")
    assert success_duplicate is False

def test_authenticate_user():
    create_user("authuser", "authpass")
    
    # Success
    assert authenticate_user("authuser", "authpass") is True
    
    # Wrong password
    assert authenticate_user("authuser", "wrongpass") is False
    
    # Non-existent user
    assert authenticate_user("unknownuser", "authpass") is False

def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    assert isinstance(token, str)
    
    # Verify token
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"
    assert "exp" in payload
