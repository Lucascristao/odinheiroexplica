# Produção do O Dinheiro Explica no chat

Quando a pessoa pedir **“Gerar o vídeo de hoje”** ou um vídeo por tema neste repositório:

1. Leia `prompts/daily-editorial.md`, `docs/editorial-continuity.md`, `docs/editorial-voice.md` e `docs/tts.md`. Pesquise a pauta atual e escreva `video/data/daily.json` com fatos verificáveis, datas, fontes específicas e imagens utilizáveis.
2. Antes de renderizar, crie um storyboard da pauta: gancho visual, objetos que persistem, percurso da câmera, mudança visual ligada a cada afirmação, provas e saída. Use a paleta do canal, mas não repita a composição do episódio anterior. `video/src/MotionDesignProof.tsx` é uma referência de linguagem, não um template a copiar.
3. Faça a direção visual funcionar no render diário de fato. Preencher `visual_direction` com texto não basta: confira os `visual.stage` e `visual.beats`, use movimentos de câmera e conexões quando explicam a relação, e crie composição específica para o episódio se o palco genérico não conseguir contar a história. Leia `docs/visual-preview.md` e revise o clip e os quadros gerados pela Action do PR antes do render completo. Isso funciona pelo GitHub, sem arquivos do computador do autor.
4. Execute validação editorial, auditoria de fontes, auditoria de pronúncia, typecheck e testes relevantes. Nunca invente recorte de fonte ou ponto de gráfico para preencher uma cena.
5. Sintetize a narração apenas com Gemini TTS. Fixe o modelo e a voz no episódio inteiro; nunca troque para outro modelo no meio do vídeo. Reutilize o cache de cenas válidas ao retomar após quota. Escute e confira a narração e sua sincronização com os elementos visuais.
6. O workflow diário envia ao Drive quando termina. Só o acione para a versão final depois de conferir o plano e a prévia visual; não use a Action de produção para testar roteiro, câmera ou TTS às cegas.

O botão no painel copia o pedido para o chat; ele não gera o vídeo por si só. O trabalho editorial e a direção de cena são parte obrigatória da tarefa do agente que recebe o pedido.
