"""Canonical Gemini Live voice policy and request configuration."""

import hashlib
import json
from pathlib import Path

VOICE_POLICY_PATH = Path(__file__).with_name("voice-policy.json")
VOICE_POLICY = json.loads(VOICE_POLICY_PATH.read_text(encoding="utf-8"))
VOICE_POLICY_VERSION = VOICE_POLICY["version"]
TTS_MODEL_CASCADE = tuple(VOICE_POLICY["model_cascade"])
if TTS_MODEL_CASCADE != ("gemini-3.8-live",):
    raise RuntimeError("Política de voz deve usar somente gemini-3.8-live.")

PRIMARY_TTS_MODEL = TTS_MODEL_CASCADE[0]
SECONDARY_TTS_MODEL = "gemini-3.8-flash-lite-tts"
FALLBACK_TTS_MODEL = "gemini-3.1-flash-tts-preview"
ELIGIBLE_FALLBACK_FAILURES = frozenset()

PRESENTER_VOICES = {
    key: value["voice"] for key, value in VOICE_POLICY["presenters"].items()
}
PRESENTER_NAMES = {
    key: value["name"] for key, value in VOICE_POLICY["presenters"].items()
}
DEFAULT_PRESENTER = VOICE_POLICY["default_presenter"]
DEFAULT_TTS_VOICE = PRESENTER_VOICES[DEFAULT_PRESENTER]
VOICE_LANGUAGE = VOICE_POLICY["language"]
VOICE_DELIVERY_STYLE = VOICE_POLICY["delivery_style"]
NO_VOICE_TREATMENT = VOICE_POLICY["raw_audio_treatment"]
MINIMUM_TRANSCRIPTION_SIMILARITY = float(
    VOICE_POLICY["minimum_transcription_similarity"]
)
DEFAULT_TTS_RATE = "0%"
DEFAULT_TTS_PITCH = "0%"
GLOBAL_PRONUNCIATIONS = {}


def project_pronunciations(project: dict | None) -> dict[str, str]:
    speech = (project or {}).get("speech") or {}
    raw = speech.get("pronunciations") or {}
    return {
        str(key).strip(): str(value).strip()
        for key, value in raw.items()
        if str(key).strip() and str(value).strip()
    }


def project_speech_fingerprint(project: dict | None) -> str:
    pronunciations = project_pronunciations(project)
    canonical = json.dumps(
        pronunciations,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def scene_voice_direction(scene: dict) -> dict:
    """Validated acting instructions; never turn old rate/pitch into processing."""
    raw = scene.get("tts") or {}
    if not isinstance(raw, dict):
        raise ValueError("tts da cena deve ser um objeto.")
    for field in ("rate", "pitch"):
        if str(raw.get(field, "0%")) not in ("0%", "+0%", "-0%"):
            raise ValueError(f"Gemini Live raw não aplica {field}; use direção de interpretação.")
    result = {}
    delivery = raw.get("delivery")
    if delivery:
        if delivery not in ("hook", "explain", "contrast", "question", "closing"):
            raise ValueError("Direção de interpretação desconhecida.")
        result["delivery"] = delivery
    if raw.get("pause_ms") is not None:
        pause = int(raw["pause_ms"])
        if not 90 <= pause <= 300:
            raise ValueError("Pausa de direção fora do intervalo editorial.")
        result["pause_ms"] = pause
    pronunciations = project_pronunciations({"speech": {"pronunciations": raw.get("pronunciations") or {}}})
    if pronunciations:
        result["pronunciations"] = pronunciations
    cues = []
    narration = str(scene.get("narration") or "")
    previous_end = -1
    for cue in sorted(raw.get("cues") or [], key=lambda c: narration.find(str(c.get("text") or ""))):
        phrase = str(cue.get("text") or "").strip()
        start = narration.find(phrase)
        kind = cue.get("kind")
        pause = int(cue.get("pause_before_ms", 0))
        if not phrase or narration.count(phrase) != 1 or start < previous_end or kind not in ("emphasis", "number", "contrast") or not 0 <= pause <= 300:
            raise ValueError("Cue vocal exige trecho literal único, válido e sem sobreposição.")
        if (start > 0 and narration[start-1].isalnum() and phrase[0].isalnum()) or (start+len(phrase) < len(narration) and narration[start+len(phrase)].isalnum() and phrase[-1].isalnum()):
            raise ValueError("Cue vocal corta uma palavra.")
        cues.append({"text": phrase, "kind": kind, "pause_before_ms": pause})
        previous_end = start + len(phrase)
    if len(cues) > 6:
        raise ValueError("Mais de seis cues vocais na cena.")
    if cues:
        result["cues"] = cues
    return result


def scene_direction_fingerprint(scene: dict) -> str | None:
    direction = scene_voice_direction(scene)
    if not direction:
        return None
    return hashlib.sha256(json.dumps({"version": "live-scene-direction-v1", "direction": direction, "instruction": live_turn_text("", direction)}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def live_turn_text(narration: str, direction: dict) -> str:
    if not direction:
        return "ROTEIRO:\n" + narration
    deliveries = {"hook": "Comece com curiosidade contida e conexão direta.", "explain": "Explique com clareza conversacional, sem tom de aula.", "contrast": "Destaque o contraste sem dramatizar.", "question": "Faça a pergunta naturalmente, sem exagerar a entonação.", "closing": "Conclua com segurança tranquila e finalize a última frase."}
    instructions = ["INSTRUÇÕES DE INTERPRETAÇÃO; NÃO LEIA ESTE BLOCO. Mantenha a voz e a postura da sessão. Esta direção vale somente para este turno; nas cenas seguintes volte à direção base se não houver instrução nova. Leia somente o ROTEIRO, sem retomar cenas anteriores. Encerre depois da última palavra, sem comentário ou despedida extra."]
    if direction.get("delivery"):
        instructions.append(deliveries[direction["delivery"]])
    if direction.get("pause_ms"):
        instructions.append(f"Pequenas pausas naturais entre ideias, aproximadamente {direction['pause_ms']} ms; isso é direção de fala, não um controle exato.")
    for term, spoken in sorted(direction.get("pronunciations", {}).items()):
        instructions.append(f"Pronúncia: {json.dumps(term, ensure_ascii=False)} como {json.dumps(spoken, ensure_ascii=False)}.")
    for cue in direction.get("cues", []):
        instructions.append(f"Trecho {json.dumps(cue['text'], ensure_ascii=False)}: {cue['kind']}; pausa natural breve antes, aproximadamente {cue['pause_before_ms']} ms. Preserve cada palavra.")
    return "\n".join(instructions) + "\n\nROTEIRO:\n" + narration


def live_system_instruction(pronunciations: dict[str, str] | None = None) -> str:
    lines = [
        "Você é o narrador do canal O Dinheiro Explica.",
        "Sua única tarefa nesta sessão é ler em voz alta, literalmente, o texto "
        "fornecido pelo usuário depois de ROTEIRO.",
        "Não cumprimente, não explique, não resuma, não reformule, não antecipe "
        "e não acrescente nenhuma palavra.",
        f"Idioma: português brasileiro ({VOICE_LANGUAGE}).",
        f"Direção de voz: {VOICE_DELIVERY_STYLE}",
        "Use a pontuação do roteiro para criar pausas naturais. Preserve números, "
        "nomes e sentido. Não leia instruções, rótulos ou delimitadores.",
    ]
    items = pronunciations or {}
    if items:
        pairs = "; ".join(
            f"{term} = {spoken}" for term, spoken in sorted(items.items())
        )
        lines.append(
            "Pronúncias obrigatórias, usadas somente para a fala e nunca como "
            f"conteúdo extra: {pairs}."
        )
    return " ".join(lines)


def live_session_config(
    voice: str,
    pronunciations: dict[str, str] | None = None,
) -> dict:
    if voice not in PRESENTER_VOICES.values():
        raise ValueError("Voz não prevista na política do canal.")
    return {
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {"voice_name": voice}
            }
        },
        "output_audio_transcription": {},
        "system_instruction": live_system_instruction(pronunciations),
        "temperature": 0.1,
    }


def gemini_speech_request(
    narration: str,
    voice: str,
    model: str,
) -> tuple[str, dict]:
    if model != PRIMARY_TTS_MODEL:
        raise ValueError("Somente gemini-3.8-live está autorizado.")
    return "live-websocket", {
        "model": model,
        "config": live_session_config(voice),
        "client_content": {
            "turns": {
                "role": "user",
                "parts": [{"text": "ROTEIRO:\n" + narration}],
            },
            "turn_complete": True,
        },
    }


def voice_policy_fingerprint(model: str, voice: str) -> str:
    if model != PRIMARY_TTS_MODEL or voice not in PRESENTER_VOICES.values():
        raise ValueError("Modelo ou voz fora da política atual.")
    canonical = json.dumps(
        {
            "version": VOICE_POLICY_VERSION,
            "model": model,
            "voice": voice,
            "config": live_session_config(voice),
            "raw_audio_treatment": NO_VOICE_TREATMENT,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


VOICE_POLICY_CACHE_KEY = hashlib.sha256(
    json.dumps(
        VOICE_POLICY,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
).hexdigest()[:16]
