import os
import requests
import base64

api_key = os.environ.get("GEMINI_API_KEY", "").strip()

models_to_test = ["gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts", "gemini-3.8-flash"]

for m in models_to_test:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Olá! Testando áudio das vozes do Gemini para O Dinheiro Explica."}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": "Puck"
                    }
                }
            }
        }
    }
    resp = requests.post(url, json=payload, timeout=60)
    print(f"Model {m} status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        audio_part = next((p for p in parts if "inlineData" in p and "data" in p["inlineData"]), None)
        if audio_part:
            raw = base64.b64decode(audio_part["inlineData"]["data"])
            mime = audio_part["inlineData"].get("mimeType", "")
            print(f"  SUCCESS! Audio received: {len(raw)} bytes, mimeType: {mime}")
            break
        else:
            print(f"  200 OK but parts structure: {parts}")
    else:
        print(f"  Error: {resp.text[:500]}")
