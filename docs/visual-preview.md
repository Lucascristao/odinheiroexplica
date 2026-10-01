# Revisão visual pelo GitHub

A produção autorizada usa diretamente a `main`. O fluxo normal é pesquisa e storyboard → validações e revisão editorial → vídeo real com Gemini 3.8 Live → revisão dos artefatos → ajustes e retomada pelo cache. Não exige PR nem acesso ao computador do autor. A publicação é manual.

Confira o MP4 final, os quadros e os relatórios do Actions/Drive. Revise textos e SVGs, rótulos das conexões, operadores, unidades, identificação dos exemplos e os quadros intermediários dos movimentos. Conferir apenas início e fim não comprova legibilidade da animação.

A Action **Prévia visual do vídeo diário** continua disponível por `workflow_dispatch` na main quando houver uma dúvida concreta de composição. PRs são opcionais. Ela prepara assets e entrega `daily-visual-preview`, sem Gemini ou envio ao Drive. O helper cria áudio silencioso e tempos estimados, identificados como `preview_only`; esse material não pode entrar no render de produção.

Uma prévia silenciosa avalia composição, movimento e leitura. Naturalidade, pronúncia, integridade e sincronização dependem do vídeo com áudio real. Não gere amostras de voz ou renders extras por obrigação. Alterações visuais aproveitam áudio válido conforme `worker/voice-policy.json`.
