"""Find a working vision-capable model for secondary gate."""

from dotenv import load_dotenv

load_dotenv()

import base64
import io
import os

import requests
from PIL import Image

key = os.getenv("GEMINI_API_KEY", "").strip()
img = Image.new("RGB", (64, 64), (40, 140, 40))
buf = io.BytesIO()
img.save(buf, format="JPEG")
b64 = base64.b64encode(buf.getvalue()).decode()

candidates = [
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-2.5-flash-image",
    "gemma-4-26b-a4b-it",
]

for model in candidates:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            'Is this a tomato leaf? Reply JSON only '
                            '{"valid": false, "object_type": "other"}'
                        )
                    },
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 64},
    }
    rr = requests.post(url, params={"key": key}, json=payload, timeout=45)
    print(model, rr.status_code)
    if rr.status_code == 200:
        text = rr.json()["candidates"][0]["content"]["parts"][0]["text"]
        print("VISION_OK", model)
        print("snippet=", text[:120].replace("\n", " "))
        break
    print("err=", rr.text[:180].replace(key, "***").replace("\n", " "))
else:
    print("RESULT=FAIL no_vision_model")
    raise SystemExit(1)

print("RESULT=PASS")
