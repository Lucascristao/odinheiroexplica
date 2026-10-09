# Giro do Dinheiro, linha de notícias (independente dos explicativos)

## Formato editorial
Três edições pretendidas, manhã/tarde/noite. Referência de cadência, não de política ou de personalidade: noticiário narrado por uma mesma pessoa, com 3 a 6 histórias diferentes por edição. **Nunca** pegar um único tema e disfarçá-lo como noticiário. Ser informativo, direto, brasileiro e conversacional: Roberto/Charon, Gemini Live, com master WAV de continuidade. Cada notícia distingue fato verificado, anúncio, projeção e risco; fatos recentes exigem fontes de publicadores diferentes e datas. Antes de atribuir consequência ao bolso, demonstrar mecanismo ou declarar incerteza. Evitar narração robotizada e leituras de manchete sem contexto.

A preparação editorial se dá em news/editions/ARQUIVO.json com status explícito de aprovação para piloto privado. O adaptador worker/news_project.py **não pesquisa, não cria fontes e não escreve notícias**; converte textos verificados em cenas do motor existente. Entram por ele a voz e seus controles de fidelidade, o compositor Remotion, o áudio contínuo, a embalagem SEO, QA técnico e o envio privado direto ao YouTube. A edição-piloto contém três matérias apuradas em 8 de outubro de 2026. A identidade gráfica fixa usa fundo carvão, #FFBD19, texto branco e composição dinâmica por matéria, sem imitar vinhetas ou bordões de outro canal.

## Como operar

- .github/workflows/render-news.yml dispara o piloto somente por push do arquivo piloto ou execução manual com um caminho aprovado. Não substitui daily.json nem altera a produção explicativa. Sempre gera MP4 e envia **somente privado**; nunca faz publicação pública automática.
- .github/workflows/news-scout.yml consulta RSS às 08h, 14h e 20h (Brasília, UTC-3) e guarda candidatos como artifact. **Não é uma redação autônoma nem agenda vídeos**, porque manchetes RSS não bastam para apuração nem existe hoje um agente editor confiável alimentando o workflow. A meta de três vídeos diários ainda depende de desenvolver e validar esse agente. Não anunciar que os três uploads diários estejam ativos.
- Depois do render, baixar e inspecionar artifact \`news-production-review\`; ler QA, assistir e ouvir o MP4 real. A imagem da capa deve ser **gerada aqui no ChatGPT**, nunca pressupor que Github Actions gera imagens automaticamente. Versionar thumbnail + thumbnail-audit baseado na imagem de verdade, usar a integração \`upload-thumbnail.yml target=youtube\` com ID privado confirmado e reportar sucesso.
- A permissão \`youtube.force-ssl\` foi autenticada em 9/10. Existe agora `publish-news.yml` para promover privado para público **somente após** capa anexada, auditoria com hash e confirmação explícita, além de revisão humana do MP4, e verificar a restrição de auditoria de projetos YouTube Data API não verificados. Não assumir que escopo OAuth remove a restrição da API. Até que isso seja concluído, a publicação deve ser manual e após revisão.
- Falha de RSS, apuração, narração, Remotion, QA, upload ou auditoria deve interromper a entrega e conservar provas para retomada. Não fabricar fontes, tempos, métricas ou confirmações de publicação.

## Anti-repetição

Cada edição mantém ID por data e período; no futuro, o agente deverá comparar URLs e eventos publicados nas edições do dia e evitar repetição entre manhã/tarde/noite. O scout sozinho ainda não efetua essa seleção. Não confundir conteúdos evergreen do explicativo com o noticiário cotidiano. O nome ANCAPSU se refere apenas à ideia geral de noticiário com múltiplos assuntos e narração fluida, não a seus posicionamentos.


### Liberação pública com force-ssl

`worker/youtube_publication.py` usa `youtube.force-ssl` junto dos escopos já autorizados. `upload-thumbnail.yml` aceita `target=youtube` para a notícia, gera o VideoProject da edição indicada e grava artifact `youtube-thumbnail-delivery`. A arte deve estar no Git, em `production/EPISODIO/thumbnail.jpg`, com `thumbnail-audit.json` gerado somente após inspecionar a imagem de verdade. A auditoria da notícia valida o SHA do VideoProject exportado por `news_project.py`, sem modificar o projeto evergreen.

Após ouvir e assistir ao MP4 e verificar a capa anexada, o editor registra `publication-approval.json` no diretório do episódio contendo `project_id,video_id,thumbnail_sha256,status:approved_for_publication,full_video_watched:true,reviewer`. Execute **manualmente** `publish-news.yml` com o ID do envio privado, o ID do envio da capa e a confirmação literal `PUBLICAR_` seguida do ID do episódio. O workflow baixa recibos reais do GitHub, valida o canal, a tag editorial, o estado privado, o hash da imagem e a revisão; chama `videos.update` somente depois. Consulta a API novamente e declara êxito apenas se o status retornar `public`. Projeto não auditado pode ficar restrito ao privado; não tentar contornar a política do YouTube.
