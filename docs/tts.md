# Narração

## Motor escolhido

Azure AI Speech.

O Kokoro foi descartado depois do teste auditivo em pt-BR.

## Referência atual

A voz preferida até aqui é:

`pt-BR-NicolauNeural`

Antes de fechar a identidade sonora, o projeto testa Nicolau contra outras vozes brasileiras.

## Segunda rodada

### Neural padrão

- `pt-BR-AntonioNeural`
- `pt-BR-DonatoNeural`
- `pt-BR-HumbertoNeural`
- `pt-BR-JulioNeural`
- `pt-BR-ValerioNeural`

### Multilingual

- `pt-BR-MacerioMultilingualNeural`

### Neural HD

- `pt-BR-Caio:MAI-Voice-2`
- `pt-BR-Pedro:MAI-Voice-2`
- `pt-BR-Rafael:MAI-Voice-2`
- `pt-BR-Luana:MAI-Voice-2`

As vozes HD são tentadas de forma opcional. Se o recurso F0 ou a região não permitir, o workflow continua e a página informa que ficaram indisponíveis.

## Custo

A camada F0 inclui 0,5 milhão de caracteres mensais para TTS Neural padrão. As vozes HD não fazem parte da franquia Neural padrão e não devem motivar mudança para S0 sem decisão explícita.

## Segredos

- `AZURE_SPEECH_KEY`
- `AZURE_SPEECH_REGION`

## Timeline

roteiro por cena → TTS por cena → duração real do áudio → timeline → render.

Cada cena terá áudio próprio para permitir regeneração isolada.
