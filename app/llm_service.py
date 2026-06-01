"""
OpenAI GPT-4o-mini integration for bilingual (Shona / English) tobacco
disease diagnosis and farming recommendations.

Two public functions:
  • get_diagnosis_from_image  – called after YOLO classification
  • get_diagnosis_from_description – called when the user describes symptoms
"""

from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any

import httpx
from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

logger = logging.getLogger(__name__)

# ── Client (lazy) ───────────────────────────────────────────────────────
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.startswith("sk-your"):
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. "
                "Please set a valid key in the .env file."
            )
        _client = AsyncOpenAI(api_key=api_key)
    return _client


# ── Shared system prompt ────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are an expert tobacco agronomist and plant pathologist specialising in \
Zimbabwean smallholder tobacco farming. You provide diagnoses and practical \
farming recommendations in both English and Shona.

## Disease Reference

| English Name           | Shona Name                                    |
|------------------------|-----------------------------------------------|
| Alternaria Alternata   | Chirwere cheAlternaria (Brown Spot / Madoadoa aBrown) |
| Cercospora Nicotianae  | Chirwere cheCercospora (Frog Eye Spot / Madoadoa eDatya) |
| Tobacco Mosaic Virus   | Chirwere cheMosaic (TMV)                      |
| Angular Leaf Spot                      | Madoadoa eAngular                                        |
| Blue Spot Fungus                       | Fangasi rinokonzera mavara ebhuruu kana grey pamashizha  |
| Hornworms / Loopworms Tobacco Damage   | Kukuvadzwa kwefodya nemakonye anodya mashizha            |
| Bacterial Leaf Drop                    | Kudonha kwemashizha kunokonzerwa nebhakitiriya           |
| Healthy                                | Yakagwinya (Mashizha akanaka)                            |

## Shona Language Examples

- "Mashizha emubatwa wenyu ane chirwere cheAlternaria."
  (Your tobacco leaves have Alternaria disease.)
- "Shandisai mushonga we fungicide sezvakanyorwa."
  (Apply fungicide as prescribed.)
- "Mashizha akanaka, enderai kuchengetedza zvakanaka."
  (Leaves are healthy, continue with good practices.)

## Vague Symptoms / Safety

If the provided symptoms are not enough for a diagnosis (e.g. "my tobacco is sick", "leaves are not looking good", "chii chingaita kuti fodya isakure zvakanaka"):
- Do not guess or assume a disease.
- Respond safely by asking the farmer clarifying questions (e.g., "Are there spots? Are leaves falling? Are there insects?").
- Recommend sending a photo or consulting an expert if the problem worsens quickly.

## Response Format

Always respond with valid JSON (no markdown fences) using this structure:
{
  "disease_name_en": "...",
  "disease_name_sn": "...",
  "description_en": "...",
  "description_sn": "...",
  "recommendations_en": ["..."],
  "recommendations_sn": ["..."],
  "confidence_note": "..."
}

Keep recommendations practical, concise (3-5 bullet points), and relevant to \
smallholder tobacco farmers in Zimbabwe. Include both cultural practices and \
chemical controls where appropriate.\
"""


# ── Public API ──────────────────────────────────────────────────────────

async def get_diagnosis_from_image(
    class_name: str,
    confidence: float,
) -> dict[str, Any]:
    """
    Generate a bilingual diagnosis after YOLO classification.

    Parameters
    ----------
    class_name : str
        Predicted class label, e.g. "Alternaria Alternata".
    confidence : float
        Model confidence (0–1).

    Returns
    -------
    dict  – structured diagnosis with bilingual fields.
    """
    if confidence < 0.60:
        user_prompt = (
            f"The AI image classifier indicated a low-confidence match ({confidence:.1%} confidence) "
            f"for **{class_name}** on a tobacco leaf.\n\n"
            "Because the confidence is low (below 60%), DO NOT give a definitive diagnosis. Instead, provide:\n"
            "1. A cautious description in English and Shona stating that the image is unclear or the symptoms are ambiguous, but it *might* be this disease or others with similar symptoms.\n"
            "2. General preventive farming recommendations in both languages.\n"
            "3. A STRONG disclaimer in both languages advising the farmer to take a clearer, closer photo in better lighting and upload it again for an accurate diagnosis."
        )
    else:
        user_prompt = (
            f"The AI image classifier detected **{class_name}** on a tobacco leaf "
            f"with {confidence:.1%} confidence.\n\n"
            "Please provide:\n"
            "1. A brief description of this condition in English and Shona.\n"
            "2. Practical farming recommendations in both languages.\n"
            "3. A note about the confidence level and whether further inspection "
            "is advised."
        )

    return await _call_llm(user_prompt)


async def get_diagnosis_from_description(
    user_text: str,
    language: str = "both",
) -> dict[str, Any]:
    """
    Diagnose from a free-text symptom description.

    Parameters
    ----------
    user_text : str
        User's description of symptoms (English or Shona).
    language : str
        Preferred response language: "en", "sn", or "both" (default).

    Returns
    -------
    dict  – structured diagnosis with bilingual fields.
    """
    lang_instruction = {
        "en": "Respond only in English.",
        "sn": "Respond only in Shona.",
        "both": "Respond in both English and Shona.",
    }.get(language, "Respond in both English and Shona.")

    user_prompt = (
        f"A tobacco farmer describes the following symptoms:\n\n"
        f'"{user_text}"\n\n'
        f"{lang_instruction}\n"
        "Based on these symptoms, identify the most likely disease from the "
        "reference table (Alternaria Alternata, Cercospora Nicotianae, TMV, Angular Leaf Spot, "
        "Blue Spot Fungus, Hornworms / Loopworms Tobacco Damage, Bacterial Leaf Drop, or Healthy) "
        "and provide your diagnosis with practical recommendations.\n"
        "If the symptoms described are completely unrelated to plants, agriculture, or tobacco, "
        "or if it is gibberish, output 'Unknown' for the disease name and ask the user to describe actual symptoms."
    )

    return await _call_llm(user_prompt)


async def check_for_new_diseases_vision(image_bytes: bytes, yolo_prediction: str) -> str | None:
    """
    Check if the image contains TMV or Angular Leaf Spot using GPT-4o-mini vision.
    Uses Chain-of-Thought reasoning to prevent false positives on Alternaria and Cercospora.
    Returns the class name if detected, else None.
    """
    try:
        client = _get_client()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = (
            "You are an expert tobacco plant pathologist. An initial classifier predicted this leaf as: "
            f"'{yolo_prediction}'.\n\n"
            "Your task is to double-check this image.\n\n"
            "FIRST, verify if the image actually shows a plant, leaf, or agriculture-related subject. If it is clearly not a plant (e.g. an animal, person, screenshot, random object), you must return 'Not a Plant' for the override_disease.\n\n"
            "SECOND, if it IS a plant, double-check if this image ACTUALLY shows clear signs of:\n"
            "1. 'Tobacco Mosaic Virus' (TMV): light/dark green mosaic patterns, mottling, or vein clearing.\n"
            "2. 'Angular Leaf Spot': dark brown/black spots that are strictly ANGULAR (straight edges bounded by leaf veins), NOT perfectly round.\n"
            "3. 'Blue Spot Fungus': fungal infection causing distinct blue or grey spots on the leaves.\n"
            "4. 'Hornworms / Loopworms Tobacco Damage': large chewed holes in leaves, missing leaf margins, and visible caterpillars/worms or insect droppings.\n"
            "5. 'Bacterial Leaf Drop': dark rotting spots leading to severe yellowing and leaves actively rotting/falling off.\n\n"
            "Important constraints:\n"
            "- 'Alternaria Alternata' (Brown Spot) has large, ROUND brown spots with concentric rings.\n"
            "- 'Cercospora Nicotianae' (Frog Eye) has ROUND spots with light/white/gray centers and dark borders.\n"
            "- If the spots are largely round, or have white centers, it is NOT Angular Leaf Spot.\n\n"
            "Respond with JSON in this format:\n"
            "{\n"
            '  "reasoning": "brief explanation of what is seen in the image",\n'
            '  "override_disease": "Tobacco Mosaic Virus" | "Angular Leaf Spot" | "Blue Spot Fungus" | "Hornworms / Loopworms Tobacco Damage" | "Bacterial Leaf Drop" | "Not a Plant" | "None"\n'
            "}\n"
            "If you see Brown Spot, Frog Eye, Healthy, or aren't absolutely sure it's one of the 5 diseases above, set override_disease to 'None'."
        )

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "low"
                            }
                        }
                    ]
                }
            ],
            max_tokens=150,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        
        override = result.get("override_disease", "None")
        valid_overrides = [
            "Tobacco Mosaic Virus", "Angular Leaf Spot", 
            "Blue Spot Fungus", "Hornworms / Loopworms Tobacco Damage", 
            "Bacterial Leaf Drop", "Not a Plant"
        ]
        if override in valid_overrides:
            return override
            
    except Exception as exc:
        logger.warning("Vision fallback check failed: %s", exc)
        
    return None

async def transcribe_audio(audio_bytes: bytes, filename: str, language: str = "both") -> str:
    """
    Transcribe audio. If Shona, uses Hugging Face's w2v-bert-2.0-shona-asr.
    If English (or fallback), uses OpenAI's Whisper API.
    """
    if language == "sn":
        # Use Hugging Face Inference API for Shona
        hf_token = os.getenv("HF_TOKEN")
        headers = {}
        if hf_token:
            headers["Authorization"] = f"Bearer {hf_token}"
            
        api_url = "https://api-inference.huggingface.co/models/badrex/w2v-bert-2.0-shona-asr"
        
        try:
            async with httpx.AsyncClient() as httpx_client:
                response = await httpx_client.post(
                    api_url, 
                    headers=headers, 
                    content=audio_bytes,
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Hugging Face ASR returns {"text": "transcription"}
                if isinstance(data, dict) and "text" in data:
                    return data["text"]
                elif isinstance(data, list) and len(data) > 0 and "text" in data[0]:
                    return data[0]["text"]
                elif "error" in data:
                    if "is currently loading" in data.get("error", ""):
                        raise RuntimeError("Shona AI model is waking up. Please wait 20 seconds and try again.")
                    raise RuntimeError(f"Hugging Face API Error: {data['error']}")
                else:
                    logger.error("Unexpected HF response: %s", data)
                    raise RuntimeError("Unexpected response from Shona ASR model.")
        except httpx.HTTPStatusError as exc:
            try:
                err_msg = exc.response.json().get("error", str(exc))
                if "is currently loading" in err_msg:
                    raise RuntimeError("Shona AI model is waking up. Please wait 20 seconds and try again.")
                logger.error("HF Inference API error: %s", err_msg)
                raise RuntimeError(f"Hugging Face API Error: {err_msg}")
            except Exception:
                logger.error("HF Inference API HTTP error: %s", exc)
                raise exc
        except Exception as exc:
            logger.error("Shona Audio transcription error: %s", exc)
            raise exc

    # Fallback to OpenAI Whisper for English (or if language is not "sn")
    client = _get_client()
    kwargs = {
        "model": "whisper-1",
        "file": (filename, audio_bytes),
    }
    if language == "en":
        kwargs["language"] = "en"
        
    try:
        response = await client.audio.transcriptions.create(**kwargs)
        return response.text
    except Exception as exc:
        logger.error("Audio transcription error (Whisper): %s", exc)
        raise exc

# ── Internal helper ─────────────────────────────────────────────────────

async def _call_llm(user_prompt: str) -> dict[str, Any]:
    """Send a chat completion request and parse the JSON response."""
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON content: %s", content[:200])
            return {
                "disease_name_en": "Unknown",
                "disease_name_sn": "Haizivikanwi",
                "description_en": content,
                "description_sn": "",
                "recommendations_en": [],
                "recommendations_sn": [],
                "confidence_note": "The AI response could not be parsed.",
            }

    except RateLimitError:
        logger.error("OpenAI rate limit exceeded")
        return _error_response(
            "The AI service is temporarily overloaded. Please try again shortly.",
            "Sevhisi yeAI yakanyanya kushandiswa. Edzai zvakare mushure menguva pfupi.",
        )
    except APIConnectionError:
        logger.error("Could not connect to OpenAI API")
        return _error_response(
            "Unable to connect to the AI service. Check your internet connection.",
            "Hatikwanisi kubatana nesevhisi yeAI. Taridzai internet yenyu.",
        )
    except APIError as exc:
        logger.error("OpenAI API error: %s", exc)
        return _error_response(
            f"AI service error: {exc.message}",
            "Sevhisi yeAI ine dambudziko. Edzai zvakare.",
        )
    except Exception as exc:
        logger.error("Unexpected LLM error: %s", exc)
        return _error_response(
            "An unexpected error occurred while generating the diagnosis.",
            "Pane dambudziko risina kutarisirwa. Edzai zvakare.",
        )


def _error_response(msg_en: str, msg_sn: str) -> dict[str, Any]:
    """Return a well-structured error payload so the frontend never breaks."""
    return {
        "disease_name_en": "Error",
        "disease_name_sn": "Kukanganisa",
        "description_en": msg_en,
        "description_sn": msg_sn,
        "recommendations_en": [],
        "recommendations_sn": [],
        "confidence_note": "",
    }
