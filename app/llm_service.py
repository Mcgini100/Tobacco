"""
OpenAI GPT-4o-mini integration for bilingual (Shona / English) tobacco
disease diagnosis and farming recommendations.

Two public functions:
  • get_diagnosis_from_image  – called after YOLO classification
  • get_diagnosis_from_description – called when the user describes symptoms
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

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
| Healthy                | Yakagwinya (Mashizha akanaka)                 |

## Shona Language Examples

- "Mashizha emubatwa wenyu ane chirwere cheAlternaria."
  (Your tobacco leaves have Alternaria disease.)
- "Shandisai mushonga we fungicide sezvakanyorwa."
  (Apply fungicide as prescribed.)
- "Mashizha akanaka, enderai kuchengetedza zvakanaka."
  (Leaves are healthy, continue with good practices.)

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
        "reference table (Alternaria Alternata, Cercospora Nicotianae, or "
        "Healthy) and provide your diagnosis with practical recommendations."
    )

    return await _call_llm(user_prompt)


# ── Internal helper ─────────────────────────────────────────────────────

async def _call_llm(user_prompt: str) -> dict[str, Any]:
    """Send a chat completion request and parse the JSON response."""
    client = _get_client()

    try:
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
