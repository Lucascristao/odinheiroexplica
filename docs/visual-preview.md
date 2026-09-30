# Prévia visual pelo GitHub

Ao abrir ou atualizar um pull request que altere o roteiro diário, o palco ou o renderer, a Action **Prévia visual do vídeo diário** valida `video/data/daily.json`, prepara as fotos e capturas documentais, monta a timeline e renderiza um trecho da primeira cena do componente `DailyEditorial`. O artifact `daily-visual-preview` contém também quadros de outras cenas e um plano que identifica os frames. A Action pode ser iniciada manualmente pelo GitHub com `workflow_dispatch`.

Esta é uma revisão de **composição, movimento e legibilidade** que funciona em uma conta GitHub sem acesso ao computador do autor. Ela não usa `GEMINI_API_KEY`, não consome a cota TTS e não envia ao Drive. O helper `worker/create_visual_preview_audio.py` cria MP3s silenciosos e um manifesto marcado `preview_only`. Cada duração e beat é estimado da narração escrita; o arquivo de abertura é renderizado com `--muted`.

O manifesto de prévia não passa em `build_render_input.py --require-gemini`. Portanto, a Action de produção continua exigindo áudio verdadeiro do mesmo modelo e voz Gemini ao longo do episódio. **A prévia não comprova duração da fala, pronúncia nem sincronização com a voz.** Essas verificações dependem do render com TTS real, depois da aprovação visual.

Fluxo para um pedido recebido por chat: produzir o roteiro e a direção visual no repositório, abrir/atualizar o PR, baixar e assistir ao artifact da prévia, corrigir o que for necessário, e só então acionar o render diário final. A Action de prévia não substitui a decisão editorial nem cria uma pauta automaticamente.
