DEFAULT_TTS_VOICE = "Charon"
DEFAULT_TTS_RATE = "0%"
DEFAULT_TTS_PITCH = "0%"

# Vozes oficiais do canal O Dinheiro Explica usando Google Gemini 3.8 Flash TTS:
# Masculina: Charon (firme, seguro, estilo âncora/especialista financeiro)
# Feminina: Autonoe (refinada, natural, estilo jornalístico elegante)
PRESENTER_VOICES = {
    "male": "Charon",
    "female": "Autonoe",
}

PRESENTER_NAMES = {
    "male": "Roberto",
    "female": "Luana",
}

DEFAULT_PRESENTER = "male"

# No Gemini TTS, o modelo pronuncia termos como 'bets', 'payment', 'fintech',
# 'Pix', 'IBS', 'CBS' naturalmente sem necessidade de grafias fonéticas artificiais.
GLOBAL_PRONUNCIATIONS = {}
