from dotenv import load_dotenv

load_dotenv()

import base64
import io
import json
import os

import requests
from PIL import Image

from ml.predict.secondary_image_verify import _build_prompt, _extract_json

key = os.getenv("GEMINI_API_KEY", "").strip()
img = Image.new("RGB", (128, 128), (30, 150, 40))
buf = io.BytesIO()
img.save(buf, "JPEG")
b64 = base64.b64encode(buf.getvalue()).decode()

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"
payload = {
    "contents": [
        {
            "parts": [
                {"text": _build_prompt("LEAF")},
                {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
            ]
        }
    ],
    "generationConfig": {"temperature": 0, "maxOutputTokens": 128},
}
r = requests.post(url, params={"key": key}, json=payload, timeout=45)
print("status", r.status_code)
body = r.json()
print(json.dumps(body, indent=2)[:2000])
try:
    text = body["candidates"][0]["content"]["parts"][0]["text"]
    print("text=", repr(text))
    print("parsed=", _extract_json(text))
except Exception as exc:
    print("extract_fail", exc)
