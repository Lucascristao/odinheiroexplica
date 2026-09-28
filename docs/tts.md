# Narração

## Motor inicial

Kokoro-82M.

Motivos:

- open weights;
- licença Apache 2.0;
- roda em CPU;
- suporte a Português Brasileiro;
- três vozes pt-BR úteis para comparação inicial.

## Vozes em teste

- `pf_dora`
- `pm_alex`
- `pm_santa`

A voz definitiva não deve ser escolhida apenas pelo nome ou por amostras de terceiros. O workflow `Teste de vozes Kokoro` gera o mesmo texto nas três vozes.

## Critérios de escolha

1. naturalidade;
2. clareza de números e nomes de empresas;
3. ritmo de documentário curto;
4. menor sensação de leitura robótica;
5. estabilidade em textos maiores.

## Timeline

A duração do vídeo nunca é estimada antes da narração.

Fluxo:

roteiro por cena → TTS por cena → duração real do áudio → timeline → render.

O áudio de cada cena será salvo separadamente para permitir regeneração sem refazer o vídeo inteiro.
