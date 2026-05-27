import sqlite3
from pathlib import Path
import os
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Path to the database file
DB_PATH = Path(__file__).resolve().parent.parent / "database.db"

# Secret key for JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-fallback-secret-key-for-dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def verify_password(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        hashed_pw = get_password_hash(password)
        cursor.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT hashed_password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return False
    
    if not verify_password(password, user[0]):
        return False
    
    return True

# Initialize database on module load
init_db()
