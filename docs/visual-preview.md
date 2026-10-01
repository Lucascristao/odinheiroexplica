# Revisão visual pelo GitHub

A produção autorizada usa diretamente a `main`. O fluxo normal é pesquisa e storyboard → validações e revisão editorial → vídeo real com Gemini 3.8 Live → revisão dos artefatos → ajustes e retomada pelo cache. Não exige PR nem acesso ao computador do autor. A publicação é manual.

O usuário pode escolher **produção direta sem testes**. Nesse caso, não executar suítes de testes localmente ou no CI, prévias silenciosas ou renders de demonstração, nem disparar esses procedimentos indiretamente. Registrar a escolha e as verificações não executadas; preservar as suítes permanentes para o modo normal. A preparação necessária do render real continua: compilação/typecheck de produção, contratos, assets, fontes, integridade de voz, alinhamento e geração. Não prometer bypass desses gates nem apresentar a produção como testes realizados. A revisão do MP4 entregue continua parte da produção.

CI e produção auditam cedo a geometria do episódio com a fonte real (`geometry-only`), antes das dependências pesadas. Esse passe adia arquivos documentais/fotos e não aprova evidência, DOM final, voz ou sincronização. A produção conserva o passe `pre-voice` com assets reais antes do TTS e o passe `final-timing` com as âncoras da narração real. Relatórios/quadros permanecem nos artifacts mesmo quando há falha, com cena, elemento, frame e orientação de reparo. Corrigir uma região não autoriza eliminar a relação explicativa só para passar.

O chat acompanha a produção com atualizações até confirmar a entrega no Drive. Um CI verde ou um render disparado não significa vídeo entregue. Se falhar, consulte a etapa e seu relatório, corrija conforme o modo solicitado e retome o commit atual pelo cache; não rerode um commit antigo que ainda contém a falha. Ao terminar, confira vídeo e pacote de publicação, informe a pasta e prossiga com a capa segundo o prompt editorial.

Confira o MP4 final, os quadros e os relatórios do Actions/Drive. Revise textos e SVGs, rótulos das conexões, operadores, unidades, identificação dos exemplos e os quadros intermediários dos movimentos. Conferir apenas início e fim não comprova legibilidade da animação.

Assista com áudio aos trechos inteiros, incluindo o intervalo depois da última entrada. Julgue o ritmo percebido: o objeto atua conforme a fala, a relação continua sendo demonstrada, a câmera muda com intenção e a pausa serve à leitura? Contar câmeras ou observar um frame isolado não demonstra movimento expressivo. Não confundir glow/traçado inicial com cadeado abrindo, terminal confirmando ou dinheiro percorrendo uma relação real.

Confira as legendas editoriais de uma ou duas palavras: correspondência literal à fala, ritmo de entrada, origem reconhecida/estimada do tempo, escala para celular e adaptação aos espaços disponíveis. Uma região vazia pode ser intencional; se ficar sem função durante uma explicação longa, reavaliar a composição. Palavra grande não pode encobrir dado, objeto em atuação ou trecho documental. Sem aprovação automática por quantidade de legendas, efeitos ou segundos.

Use os diagnósticos de segundos sem eventos e de transformações como apoio à revisão. Eles descrevem os contratos e tempos disponíveis, não certificam amplitude visível, originalidade ou compreensão. `production_review_pending` continua pendente até a revisão do MP4 real; aprovação de fonte/layout e quadros técnicos não substitui essa etapa.

A Action **Prévia visual do vídeo diário** continua disponível por `workflow_dispatch` na main quando houver uma dúvida concreta de composição. PRs são opcionais. Ela prepara assets e entrega `daily-visual-preview`, sem Gemini ou envio ao Drive. O helper cria áudio silencioso e tempos estimados, identificados como `preview_only`; esse material não pode entrar no render de produção.

Uma prévia silenciosa avalia composição, movimento e leitura. Naturalidade, pronúncia, integridade e sincronização dependem do vídeo com áudio real. Não gere amostras de voz ou renders extras por obrigação. Alterações visuais aproveitam áudio válido conforme `worker/voice-policy.json`.
