DEFAULT_TTS_VOICE = "pt-BR-MacerioMultilingualNeural"
DEFAULT_TTS_RATE = "-2%"
DEFAULT_TTS_PITCH = "0%"

# Vozes escolhidas para os dois apresentadores fixos do canal.
# Os nomes/personagens editoriais serão definidos separadamente da voz técnica.
PRESENTER_VOICES = {
    "male": "pt-BR-MacerioMultilingualNeural",
    "female": "pt-BR-ThalitaMultilingualNeural",
}

PRESENTER_NAMES = {
    "male": "Roberto",
    "female": "Luana",
}

DEFAULT_PRESENTER = "male"

# Correções de pronúncia que só afetam a fala, sem alterar o texto publicado.
# "bet/bets" precisam soar com a vogal final audível, como "béte/bétes" em português brasileiro.
GLOBAL_PRONUNCIATIONS = {
    "bet": "béte",
    "bets": "bétes",
}
