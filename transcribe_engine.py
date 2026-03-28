"""
transcribe_engine.py
====================
Core AI transcription and translation logic for the Antiquities Service Archive.
Sends a single document image to the Gemini API and returns a structured JSON dict.
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
    ".png": "image/png",
    ".tif": "image/tiff", ".tiff": "image/tiff",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
}

# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert archival historian, palaeographer, and \
translator specializing in early 20th-century Egyptian administrative records, \
specifically the archives of the Egyptian Antiquities Service (Service des Antiquités de l'Égypte) \
from the 1920s.

You are processing typed and handwritten official correspondence. These documents \
are primarily typed in French on official letterhead, but frequently feature \
handwritten Arabic administrative notes in the margins, as well as official ink stamps.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOCUMENT CONTEXT & COMMON ENTITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Based on the archive's specific history, you will encounter the following:
- Senders (Directors General): P. Lacau, C.C. Edgar, G. Daressy.
- Primary Recipient: Monsieur E. Baraize (Directeur de Travaux du Service des Antiquités).
- Duty Stations: Poste des Pyramides (Giza), Abydos (Balianah), Louxor, Tounah.
- Key Elements: References to previous letters (e.g., "lettre N° 244"), equipment \
  dimensions, personnel management, and site administration.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRANSCRIPTION & TRANSLATION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. BILINGUAL TRANSCRIPTION: You MUST transcribe both the French and the Arabic text. \
   Provide a highly accurate, verbatim transcription. Preserve line breaks and \
   administrative formatting (e.g., placing the date "Le Caire, le..." accurately).

2. MARGINALIA & STAMPS: Do not ignore handwriting or stamps. \
   - When transcribing handwritten Arabic notes, prefix them with [Handwritten Arabic: ]. \
   - When you see an ink stamp, indicate it with [Stamp: text of stamp]. \
   - When you see pencil marks/underlines, indicate it with [Pencil note: text].

3. ENGLISH TRANSLATION: Provide a clear, professional English translation of the \
   ENTIRE document, including translating the French body and the Arabic marginalia. \
   Ensure historical bureaucratic phrasing is translated cleanly.

4. METADATA EXTRACTION: 
   - Document_Date: Standardize to YYYY-MM-DD. (e.g., "11 Mars 1926" -> 1926-03-11).
   - Sender & Recipient: Include their titles if present (e.g., "E. Baraize, Directeur de Travaux").

5. UNCERTAINTY: If a signature or word is genuinely illegible, write [?] and explain \
   your best guess in the Confidence_Notes.

6. OUTPUT FORMAT: Output ONLY valid JSON. No markdown fences. The response must begin \
   with { and end with }.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT SCHEMA (strict JSON)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{
  "Document_Date":          "<YYYY-MM-DD | null>",
  "Sender":                 "<Name and title of sender | null>",
  "Recipient":              "<Name, title, and location of recipient | null>",
  "Brief_Summary":          "<A 1-2 sentence English summary of the correspondence>",
  "Original_Transcription": "<Complete verbatim transcription, including [Stamp: ...] and [Handwritten Arabic: ...] tags>",
  "English_Translation":    "<Complete English translation of both the French and Arabic text>",
  "Stamps_and_Annotations": ["<Array of strings describing stamps or marginalia, e.g., 'Purple oval stamp: Egyptian Government', 'Red pencil note: Abydos'>"],
  "Confidence_Notes":       "<Brief notes on illegible signatures, ambiguous phrasing, or physical damage | null>"
}
"""

# ── Helpers ──────────────────────────────────────────────────────────────────

def _recover_truncated_json(raw: str) -> dict | None:
    s = raw.rstrip()
    depth_brace = s.count('{') - s.count('}')
    depth_bracket = s.count('[') - s.count(']')
    
    in_string = False
    i = 0
    while i < len(s):
        if s[i] == '"' and (i == 0 or s[i-1] != '\\'):
            in_string = not in_string
        i += 1
    if in_string:
        s += '"'
        
    s += ']' * max(0, depth_bracket)
    s += '}' * max(0, depth_brace)
    
    try:
        result = json.loads(s)
        if isinstance(result, dict):
            existing_note = result.get('Confidence_Notes') or ''
            result['Confidence_Notes'] = (
                '[TRUNCATED RESPONSE — review transcriptions for completeness] '
                + existing_note
            ).strip()
            result['_review_status'] = 'error'
        return result
    except Exception:
        return None

def _mime_from_filename(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return _MIME_MAP.get(ext, "image/jpeg")

def _mime_from_bytes(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:2] == b"\xff\xd8":
        return "image/jpeg"
    if data[:4] == b"RIFF" or data[8:12] == b"WEBP":
        return "image/webp"
    if data[:2] in (b"MM", b"II"):
        return "image/tiff"
    if data[:2] == b"BM":
        return "image/bmp"
    return "image/jpeg"

def _encode_image(image_input, filename: str = "document.jpg"):
    if isinstance(image_input, (str, Path)):
        p = Path(image_input)
        raw = p.read_bytes()
        mime = _mime_from_filename(p.name)
        source_name = p.name
    else:
        raw = bytes(image_input)
        ext = Path(filename).suffix.lower()
        mime = _MIME_MAP.get(ext) or _mime_from_bytes(raw)
        source_name = filename

    b64 = base64.standard_b64encode(raw).decode("utf-8")
    return b64, mime, source_name

def build_client(api_key: str | None = None, base_url: str | None = None) -> OpenAI:
    key = api_key or os.environ.get("OPENAI_API_KEY", "")
    url = base_url or os.environ.get(
        "OPENAI_BASE_URL",
        "[https://generativelanguage.googleapis.com/v1beta/openai/](https://generativelanguage.googleapis.com/v1beta/openai/)",
    )
    return OpenAI(api_key=key, base_url=url)

# ── Main transcription function ───────────────────────────────────────────────

def transcribe_image(
    image_input,
    client: OpenAI,
    model: str = DEFAULT_MODEL,
    filename: str = "document.jpg",
) -> dict:
    b64, mime, source_name = _encode_image(image_input, filename=filename)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{b64}",
                        "detail": "high",
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "Please analyze this archival document. Provide a verbatim transcription "
                        "in the original language, an English translation, and extract the required metadata. "
                        "Pay close attention to any handwritten marginalia or stamps. "
                        "Return the result strictly as the JSON object described in your instructions."
                    ),
                },
            ],
        },
    ]

    raw = ""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=8192,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if content is None:
            return {
                "error": "Model returned empty content. Try again or switch to a different model.",
                "_source_image": source_name,
                "_model": model,
                "_review_status": "error",
            }

        raw = content.strip()
        
        # Strip accidental markdown fences using hex to avoid parser bugs
        raw = re.sub(r"^\x60\x60\x60(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*\x60\x60\x60$", "", raw)

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = _recover_truncated_json(raw)
            if result is None:
                raise

        if "Stamps_and_Annotations" not in result:
            result["Stamps_and_Annotations"] = []

        result["_source_image"] = source_name
        result["_model"] = model
        result["_review_status"] = "pending"
        return result

    except json.JSONDecodeError as exc:
        return {
            "error": f"JSON parse error: {exc}",
            "raw_response": raw,
            "_source_image": source_name,
            "_model": model,
            "_review_status": "error",
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "_source_image": source_name,
            "_model": model,
            "_review_status": "error",
        }
