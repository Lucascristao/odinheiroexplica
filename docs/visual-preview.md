# Revisão visual pelo GitHub

A produção autorizada usa diretamente a `main`. O fluxo normal é pesquisa e storyboard → validações e revisão editorial → vídeo real com Gemini 3.8 Live → revisão dos artefatos → ajustes e retomada pelo cache. Não exige PR nem acesso ao computador do autor. A publicação é manual.

CI e produção auditam cedo a geometria do episódio com a fonte real (`geometry-only`), antes das dependências pesadas. Esse passe adia arquivos documentais/fotos e não aprova evidência, DOM final, voz ou sincronização. A produção conserva o passe `pre-voice` com assets reais antes do TTS e o passe `final-timing` com as âncoras da narração real. Relatórios/quadros permanecem nos artifacts mesmo quando há falha, com cena, elemento, frame e orientação de reparo. Corrigir uma região não autoriza eliminar a relação explicativa só para passar.

O chat acompanha a produção com atualizações até confirmar a entrega no Drive. Um CI verde ou um render disparado não significa vídeo entregue. Se falhar, consulte a etapa e seu relatório, corrija, valide o commit atual e retome pelo cache; não rerode um commit antigo que ainda contém a falha. Ao terminar, confira vídeo e pacote de publicação, informe a pasta e prossiga com a capa segundo o prompt editorial.

Confira o MP4 final, os quadros e os relatórios do Actions/Drive. Revise textos e SVGs, rótulos das conexões, operadores, unidades, identificação dos exemplos e os quadros intermediários dos movimentos. Conferir apenas início e fim não comprova legibilidade da animação.

A Action **Prévia visual do vídeo diário** continua disponível por `workflow_dispatch` na main quando houver uma dúvida concreta de composição. PRs são opcionais. Ela prepara assets e entrega `daily-visual-preview`, sem Gemini ou envio ao Drive. O helper cria áudio silencioso e tempos estimados, identificados como `preview_only`; esse material não pode entrar no render de produção.

Uma prévia silenciosa avalia composição, movimento e leitura. Naturalidade, pronúncia, integridade e sincronização dependem do vídeo com áudio real. Não gere amostras de voz ou renders extras por obrigação. Alterações visuais aproveitam áudio válido conforme `worker/voice-policy.json`.
