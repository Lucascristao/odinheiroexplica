import os
import requests

api_key = os.environ.get("GEMINI_API_KEY", "").strip()
print(f"API key length: {len(api_key)}")

# 1. List models
resp = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}")
print(f"List models status: {resp.status_code}")
if resp.status_code == 200:
    models = resp.json().get("models", [])
    print(f"Total models: {len(models)}")
    for m in models:
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            print(f"- {m['name']} (displayName: {m.get('displayName')})")
else:
    print(resp.text)

# 2. Test generateContent with AUDIO on gemini-2.0-flash
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
payload = {
    "contents": [{"parts": [{"text": "Diga apenas: Testando áudio do Gemini."}]}],
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
resp2 = requests.post(url, json=payload)
print(f"gemini-2.0-flash status: {resp2.status_code}")
print(resp2.text[:1000])
