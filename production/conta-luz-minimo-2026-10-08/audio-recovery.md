# Diagnóstico e recuperação do render de 08/10/2026

Episódio: `conta-luz-minimo-2026-10-08`.

## Evidência da falha

- Origem: workflow run `37850997426`, falhou na construção da timeline após gerar WAVs.
- O WAV `scene-01.wav` tinha **1,02 s**, enquanto a estimativa era **27,097 s**.
- A resposta textual do Gemini Live continha o roteiro completo (fidelidade lexical 1.0), mas o arquivo PCM tinha só 48.960 bytes, correspondentes a 1,02 s mono 24 kHz 16-bit.
- Alinhamento no áudio real: 0/11 âncoras da cena 1, cobertura da transcrição de áudio ~4,29%. Não é correto aprovar a transcrição declarada pelo servidor como prova de áudio completo.
- As cenas 2 a 8 geraram WAVs mais longos e chegaram ao alinhamento.
- A timeline estimava âncoras da cena 1 num intervalo de 1,02 s; o validador corretamente bloqueou beats no mesmo frame.
- Não resolver afrouxando a validação visual nem comprimindo toda a fala num segundo.

## Correção

- Nova checagem conservadora de duração PCM pelo tamanho do texto em `worker/synthesize_scenes.py` antes de gravar o WAV e de declarar sucesso. Resposta muito curta é erro transitório para retry no mesmo modelo e voz.
- O validador de cache `cached_duration` rejeita o WAV antigo que não respeita o mínimo; preserva áudios válidos.
- Os testes de regressão cobrem áudio truncado apesar de transcrição completa e cache anterior.
- Não houve troca de voz, normalização, efeitos ou corte de roteiro.

## Retomada controlada

Após novo CI **do mesmo commit** aprovado, emitir `npm run ode -- dispatch` com esta solicitação explícita. O cache Gemini Live é recuperado pelo `actions/cache/restore` com a chave de política da voz; a cena 1 será regenerada por falhar no piso PCM, e as cenas 2 a 8 serão reutilizadas se forem compatíveis. O comando `ode resume --run-id 37850997426` faria `gh run rerun --failed` do mesmo código *antigo* e não levaria a correção. Por isso a retomada usa novo run no novo SHA, mantendo caches compatíveis, sem force_fresh_audio.

Produção continua incompleta até MP4 real, revisão, capa e readbacks na mesma pasta Drive.
