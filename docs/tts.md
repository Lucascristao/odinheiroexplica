# Narração

## Motor escolhido

Azure AI Speech.

O Kokoro foi descartado depois do teste auditivo em pt-BR.

## Voz oficial do canal

A voz escolhida para o O Dinheiro Explica é:

`pt-BR-MacerioMultilingualNeural`

Ela substitui Nicolau como referência e passa a ser a voz padrão dos próximos testes e da futura geração de áudio por cena.

## Configuração atual

- voz: `pt-BR-MacerioMultilingualNeural`
- velocidade: `-2%`
- pitch: `0%`

Esses parâmetros podem ser refinados depois de ouvir roteiros maiores, mas a identidade sonora base fica definida no Macerio.

## Segredos

- `AZURE_SPEECH_KEY`
- `AZURE_SPEECH_REGION`

A chave nunca deve entrar no frontend, no repositório ou em logs.

## Timeline

roteiro por cena → TTS por cena → duração real do áudio → timeline → render.

Cada cena terá áudio próprio para permitir regeneração isolada.
