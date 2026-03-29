# transcribe_selim.py (Parallel Version)
# ==================================
# Processes a folder of scanned Arabic archival documents in parallel, sending 
# multiple concurrent requests to the Gemini API for high-throughput translation.

import asyncio
import json
import os
import time
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_random_exponential
from tqdm.asyncio import tqdm_asyncio

# --- Local Imports ---
# UPDATE THIS IMPORT to match the name of your Selim Hassan engine file.
# For example, if your file is selim_engine.py, use: import selim_engine
import transcribe_engine_selim as engine 

# --- Configuration ---
CONCURRENCY_LIMIT = 20

RETRY_CONFIG = {
    "wait": wait_random_exponential(multiplier=1, max=60),
    "stop": stop_after_attempt(5),
}

# --- Core Transcription Logic ---

@retry(**RETRY_CONFIG)
async def process_single_image(client: httpx.AsyncClient, image_path: Path, model: str, base_url: str, api_key: str) -> dict:
    """Sends one image to the API and returns the parsed JSON response or an error dict."""
    try:
        # Using the exact 3-variable unpack we fixed earlier
        encoded_image, mime_type, source_name = engine._encode_image(image_path)
        if not encoded_image:
            return {"error": "Could not encode image"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": engine.SYSTEM_PROMPT,},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"},
                        },
                        {
                            "type": "text",
                            "text": "Please transcribe and translate the attached Arabic archival document. Pay close attention to the handwriting nuances of the Qufti foremen and the Selim Hassan archives as specified in the system prompt.",
                        },
                    ],
                },
            ],
            "max_tokens": 8192,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        response = await client.post(f"{base_url}chat/completions", headers=headers, json=payload, timeout=120)
        response.raise_for_status() 

        content = response.json()["choices"][0]["message"]["content"]
        if not content:
            return {"error": "API returned empty response"}

        try:
            data = json.loads(content)
            data["_model"] = model
            return data
        except json.JSONDecodeError as e:
            recovered_data = engine._recover_truncated_json(content)
            if recovered_data:
                recovered_data["_model"] = model
                _existing_note = recovered_data.get('Confidence_Notes', '') or ''
                recovered_data['Confidence_Notes'] = f'[RECOVERED FROM TRUNCATION] {_existing_note}'.strip()
                return recovered_data
            return {"error": f"JSON parse error: {e}"}

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}


async def batch_processor(image_paths: list[Path], model: str, base_url: str, api_key: str, skip_existing: bool):
    """Processes a list of images in parallel with a progress bar and concurrency limit."""
    # Saves to a dedicated selim_transcriptions folder
    output_dir = Path(__file__).parent / "data" / "selim_transcriptions"
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks_to_run = []
    for image_path in image_paths:
        json_path = output_dir / f"{image_path.stem}.json"
        if skip_existing and json_path.exists():
            continue
        tasks_to_run.append(image_path)

    if not tasks_to_run:
        print("All documents already have transcriptions. Use --overwrite to re-process.")
        return

    print(f"Found {len(tasks_to_run)} documents to process (out of {len(image_paths)} total).")

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    processed_count = 0
    error_count = 0

    async def worker(image_path: Path, client: httpx.AsyncClient):
        nonlocal processed_count, error_count
        async with semaphore:
            result = await process_single_image(client, image_path, model, base_url, api_key)
            json_path = output_dir / f"{image_path.stem}.json"
            if "error" in result:
                error_count += 1
                json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            else:
                processed_count += 1
                json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    async with httpx.AsyncClient() as client:
        tasks = [worker(p, client) for p in tasks_to_run]
        await tqdm_asyncio.gather(*tasks, desc="Translating documents", unit="doc")

    return processed_count, error_count


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch translate Arabic archival documents in parallel.")
    parser.add_argument("path", type=Path, help="Path to a single image or a directory of images.")
    parser.add_argument("--model", default=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"), help="Name of the model to use (e.g., gemini-2.5-pro)")
    parser.add_argument("--skip-existing", "--skip", action="store_true", help="Skip images that already have a .json file.")
    parser.add_argument("--overwrite", action="store_true", help="Force re-processing of all images.")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")

    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        return

    if args.path.is_dir():
        image_paths = sorted([p for p in args.path.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")])
    elif args.path.is_file():
        image_paths = [args.path]
    else:
        print(f"Error: Path not found: {args.path}")
        return

    if not image_paths:
        print(f"No documents found in {args.path}")
        return

    start_time = time.monotonic()
    processed, errors = asyncio.run(batch_processor(image_paths, args.model, base_url, api_key, args.skip_existing and not args.overwrite))
    end_time = time.monotonic()

    total_time = end_time - start_time
    total_processed = processed + errors
    docs_per_minute = (total_processed / total_time * 60) if total_time > 0 else 0

    print("\n--- Batch Complete ---")
    print(f"Successfully processed:   {processed}")
    print(f"Errors:                   {errors}")
    print(f"Total time:               {total_time:.2f} seconds")
    print(f"Average speed:            {docs_per_minute:.2f} docs/minute")
    print("----------------------")

if __name__ == "__main__":
    main()
