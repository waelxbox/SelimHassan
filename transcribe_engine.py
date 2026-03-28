"""
transcribe_engine.py (Two-Pass Edition)
======================================
Splits the archival process into two stages to prevent token truncation:
Pass 1: Vision-based verbatim transcription (Original French/Arabic).
Pass 2: Text-based translation and metadata extraction.
"""

import base64
import json
import os
import re
from pathlib import Path
from openai import OpenAI

# ── Constants ────────────────────────────────────────────────────────────────

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.0-pro")

_MIME_MAP = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png", ".tif": "image/tiff", 
    ".tiff": "image/tiff", ".bmp": "image/bmp", ".webp": "image/webp",
}

# ── System Prompts ────────────────────────────────────────────────────────────

PROMPT_PASS_1 = """You are an expert archival palaeographer. 
Your ONLY task is to provide a highly accurate, verbatim transcription of the provided 1920s Egyptian Antiquities Service document.

1. Transcribe the French body text and any handwritten Arabic marginalia.
2. Maintain the layout (date, headers, signature placement).
3. Include markers for: [Stamp: text], [Handwritten Arabic: text], [Pencil note: text].
4. Output ONLY the raw transcription text. No summary, no translation, no intro."""

PROMPT_PASS_2 = """You are an expert archival historian and translator. 
You will be provided with a raw transcription of a 1920s Egyptian Antiquities Service document.
Your task is to translate it into English and extract structured metadata.

Use the following context:
- Senders: P. Lacau, C.C. Edgar, G. Daressy, Jean Capart.
- Recipient: Monsieur E. Baraize (Directeur de Travaux).

OUTPUT SCHEMA (STRICT JSON):
{
  "Reference_Number": "<e.g. N° 27.2/30 | null>",
  "Document_Date": "<YYYY-MM-DD | null>",
  "Sender": "<Name and title | null>",
  "Recipient": "<Name, title, and location | null>",
  "Excavation_Site": "<Specific archaeological site | null>",
  "Entities_Mentioned": ["<Array of names/orgs>"],
  "Thematic_Tags": ["<Array of 2-4 tags>"],
  "Brief_Summary": "<1-2 sentence English summary>",
  "English_Translation": "<Complete English translation of all text>",
  "Stamps_and_Annotations": ["<Array of descriptions>"],
  "Confidence_Notes": "<Notes on illegibility | null>"
}

Output ONLY valid JSON. No markdown fences."""

# ── Internal Helpers ──────────────────────────────────────────────────────────

def _encode_image(image_input, filename: str = "document.jpg"):
    if isinstance(image_input, (str, Path)):
        raw = Path(image_input).read_bytes()
        source_name = Path(image_input).name
    else:
        raw = bytes(image_input)
        source_name = filename
    b64 = base64.standard_b64encode(raw).decode("utf-8")
    return b64, source_name

def build_client(api_key: str | None = None, base_url: str | None = None) -> OpenAI:
    key = api_key or os.environ.get("OPENAI_API_KEY", "")
    url = base_url or os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    return OpenAI(api_key=key, base_url=url)

# ── Pipeline Stages ───────────────────────────────────────────────────────────

def _pass_1_transcribe(client, model, b64, mime):
    """Vision Pass: Get verbatim text."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT_PASS_1},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"}},
                {"type": "text", "text": "Verbatim transcription of all French and Arabic text, please."}
            ]}
        ],
        temperature=0.0,
        max_tokens=4000
    )
    return response.choices[0].message.content

def _pass_2_translate(client, model, original_text):
    """Text Pass: Translate and extract metadata."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT_PASS_2},
            {"role": "user", "content": f"Transcription to process:\n\n{original_text}"}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    raw_json = response.choices[0].message.content.strip()
    # Clean possible markdown fences
    raw_json = re.sub(r"^\x60\x60\x60(?:json)?\s*", "", raw_json)
    raw_json = re.sub(r"\s*\x60\x60\x60$", "", raw_json)
    
    return json.loads(raw_json)

# ── Main Function ─────────────────────────────────────────────────────────────

def transcribe_image(image_input, client: OpenAI, model: str = DEFAULT_MODEL, filename: str = "document.jpg") -> dict:
    b64, source_name = _encode_image(image_input, filename)
    mime = _MIME_MAP.get(Path(source_name).suffix.lower(), "image/jpeg")

    try:
        # STEP 1: VERBATIM TRANSCRIPTION
        original_text = _pass_1_transcribe(client, model, b64, mime)
        
        # STEP 2: TRANSLATION & METADATA
        result = _pass_2_translate(client, model, original_text)

        # Merge original transcription back into final result
        result["Original_Transcription"] = original_text
        result["_source_image"] = source_name
        result["_model"] = model
        result["_review_status"] = "pending"
        
        # Safety checks for arrays
        for field in ["Stamps_and_Annotations", "Entities_Mentioned", "Thematic_Tags"]:
            if field not in result: result[field] = []

        return result

    except Exception as exc:
        return {
            "error": str(exc),
            "_source_image": source_name,
            "_model": model,
            "_review_status": "error"
        }
