# Narração

## Motor escolhido

Azure AI Speech, usando vozes neurais nativas de Português do Brasil.

A escolha substitui o Kokoro depois do teste auditivo inicial mostrar pronúncia inadequada para o padrão do canal.

## Por que Azure

A prioridade é naturalidade em pt-BR, estabilidade e licença adequada para um canal que pretende monetizar.

A camada gratuita F0 do Azure Speech oferece 0,5 milhão de caracteres neurais por mês. Para permanecer nessa faixa gratuita, usamos vozes Neural padrão, não as novas vozes HD.

## Voz padrão inicial

`pt-BR-FranciscaNeural`

Ela fica como padrão provisório por ter boa reputação específica entre usuários brasileiros. Antes de fechar a identidade sonora do canal, o teste compara também:

- `pt-BR-FabioNeural`
- `pt-BR-NicolauNeural`

A voz final continua sendo uma decisão auditiva.

## Segredos necessários no GitHub

O workflow usa apenas GitHub Secrets:

- `AZURE_SPEECH_KEY`
- `AZURE_SPEECH_REGION`

A chave nunca deve entrar no frontend, no repositório ou em logs.

## Teste

O workflow `Teste de vozes Azure pt-BR` gera os três MP3 diretamente pela API oficial do Azure e os publica em `public/voice-tests/`.

Página de audição:

`/voice-tests/`

## Timeline

A duração do vídeo não é definida antes da narração.

Fluxo:

roteiro por cena → TTS por cena → duração real do áudio → timeline → render.

Cada cena terá seu áudio próprio para permitir regeneração isolada.
