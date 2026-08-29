"""One-off Gemini key connectivity check. Does not print the raw API key."""

from dotenv import load_dotenv

load_dotenv()

import os
import requests

key = os.getenv("GEMINI_API_KEY", "").strip()
model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip() or "gemini-3.6-flash"

print("configured=", bool(key))
print("key_prefix=", (key[:4] + "...") if key else "NONE")
print("key_len=", len(key))
print("model=", model)

if not key:
    print("RESULT=FAIL missing_key")
    raise SystemExit(1)

r = requests.get(
    "https://generativelanguage.googleapis.com/v1beta/models",
    params={"key": key},
    timeout=20,
)
print("list_models_status=", r.status_code)
if r.status_code >= 400:
    print("list_models_error=", r.text[:400].replace(key, "***"))
else:
    names = [m.get("name", "") for m in r.json().get("models", [])]
    flash = [n for n in names if "flash" in n.lower()][:8]
    print("flash_models_sample=", flash)

url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
payload = {
    "contents": [{"parts": [{"text": 'Reply with JSON only: {"ok": true}'}]}],
    "generationConfig": {"temperature": 0, "maxOutputTokens": 32},
}
r2 = requests.post(url, params={"key": key}, json=payload, timeout=30)
print("generate_status=", r2.status_code)
if r2.status_code >= 400:
    print("generate_error=", r2.text[:500].replace(key, "***"))
    print("RESULT=FAIL generate")
    raise SystemExit(2)

try:
    parts = r2.json()["candidates"][0]["content"].get("parts") or []
    text = next((p.get("text") for p in parts if isinstance(p, dict) and p.get("text")), None)
    if not text:
        raise KeyError("parts/text")
    print("generate_ok=True")
    print("generate_snippet=", text[:100].replace("\n", " "))
    print("RESULT=PASS")
except Exception as exc:
    print("generate_parse_fail=", type(exc).__name__, str(exc)[:120])
    # Auth already succeeded (HTTP 200). Treat as soft pass for key validity.
    if r2.status_code == 200:
        print("RESULT=PASS key_valid_generate_http_200")
    else:
        print("RESULT=FAIL parse")
        raise SystemExit(3)
