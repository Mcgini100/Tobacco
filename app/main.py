"""
FastAPI application for Tobacco Leaf Disease Detection.

Endpoints
---------
GET  /              – Serve the frontend (index.html)
POST /api/diagnose  – Upload an image for YOLO classification + LLM diagnosis
POST /api/describe  – Submit a text description for LLM-based diagnosis
GET  /api/health    – Health check
"""

import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi import _rate_limit_exceeded_handler  # noqa: F401 (unused re-export)
from slowapi.errors import RateLimitExceeded

from app.classifier import predict
from app.llm_service import get_diagnosis_from_image, get_diagnosis_from_description
from app.rate_limiter import limiter, DEFAULT_RATE, rate_limit_exceeded_handler
from app.database import create_user, authenticate_user, create_access_token, SECRET_KEY, ALGORITHM
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

# ── Environment & logging ───────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
)
logger = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"

# ── Constants ───────────────────────────────────────────────────────────
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# ── App factory ─────────────────────────────────────────────────────────
app = FastAPI(
    title="Tobacco Leaf Disease Detection API",
    description=(
        "Upload a tobacco leaf image or describe symptoms to receive an "
        "AI-powered bilingual (English / Shona) diagnosis with practical "
        "farming recommendations."
    ),
    version="1.0.0",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS – allow all origins during development; tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (CSS, JS, images served by the frontend)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Pydantic models ────────────────────────────────────────────────────

class DescribeRequest(BaseModel):
    """Payload for the text-based diagnosis endpoint."""
    text: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Free-text description of symptoms observed on the tobacco leaves.",
    )
    language: str = Field(
        default="both",
        pattern=r"^(en|sn|both)$",
        description="Preferred response language: 'en', 'sn', or 'both'.",
    )

class UserAuth(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


# ── Routes ──────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve the single-page frontend."""
    if not INDEX_HTML.exists():
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "Frontend not deployed yet. The static/index.html file is missing.",
            },
        )
    return FileResponse(str(INDEX_HTML))

@app.post("/api/register")
async def register(user: UserAuth):
    success = create_user(user.username, user.password)
    if not success:
        raise HTTPException(status_code=400, detail="Username already registered")
    return {"success": True, "message": "User created successfully"}

@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not authenticate_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/diagnose")
@limiter.limit(DEFAULT_RATE)
async def diagnose_image(
    request: Request,
    file: UploadFile = File(..., description="Tobacco leaf image (JPEG, PNG, or WebP, max 10 MB)"),
    current_user: str = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Accept a leaf image, classify it with YOLOv8, and return a bilingual
    diagnosis generated by GPT-4o-mini.
    """
    # ── Validate content type ────────────────────────────────────────────
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: {file.content_type}. "
                f"Allowed types: JPEG, PNG, WebP."
            ),
        )

    # ── Read & validate size ─────────────────────────────────────────────
    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(image_bytes) / 1024 / 1024:.1f} MB). Maximum is 10 MB.",
        )

    # ── Classify ─────────────────────────────────────────────────────────
    try:
        prediction = predict(image_bytes)
    except FileNotFoundError as exc:
        logger.error("Model not found: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        logger.error("Classification error: %s", exc)
        raise HTTPException(status_code=500, detail="Classification model failed. Please try again.")

    # ── LLM diagnosis ────────────────────────────────────────────────────
    try:
        diagnosis = await get_diagnosis_from_image(
            class_name=prediction["class_name"],
            confidence=prediction["confidence"],
        )
    except Exception as exc:
        logger.error("LLM diagnosis error: %s", exc)
        diagnosis = {
            "disease_name_en": prediction["class_name"],
            "disease_name_sn": "",
            "description_en": "AI diagnosis unavailable. See classification results below.",
            "description_sn": "",
            "recommendations_en": [],
            "recommendations_sn": [],
            "confidence_note": "",
        }

    return {
        "success": True,
        "prediction": prediction,
        "diagnosis": diagnosis,
    }


@app.post("/api/describe")
@limiter.limit(DEFAULT_RATE)
async def describe_symptoms(
    request: Request,
    body: DescribeRequest,
    current_user: str = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Accept a free-text symptom description and return an LLM-generated
    bilingual diagnosis.
    """
    try:
        diagnosis = await get_diagnosis_from_description(
            user_text=body.text,
            language=body.language,
        )
    except Exception as exc:
        logger.error("LLM description error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate diagnosis from description. Please try again.",
        )

    return {
        "success": True,
        "diagnosis": diagnosis,
    }


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Lightweight health check for monitoring and load balancers."""
    model_available = (BASE_DIR / "models" / "best.pt").exists()

    return {
        "status": "healthy",
        "model_loaded": model_available,
        "version": app.version,
    }


# ── Global exception handler ───────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all so unhandled errors still return JSON, not HTML."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An internal server error occurred. Please try again later.",
        },
    )


# ── Dev entry-point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
