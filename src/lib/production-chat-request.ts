export function productionChatRequest(request: string): string {
  return `${request}

Use o sistema https://github.com/Lucascristao/odinheiroexplica e leia as instruções atuais de AGENTS.md, prompts/daily-editorial.md, docs/editorial-motion-library.md e docs/visual-preview.md. Crie direção de voz, câmera e motion graphics própria para esta pauta, preservando o tema escolhido.

Planeje o movimento durante a explicação inteira, com atuação de objetos, relações e transformações pertinentes; entradas rápidas seguidas de listas paradas não bastam. Escolha legendas editoriais modernas de uma ou duas palavras sincronizadas à fala e colocadas nos espaços disponíveis quando ajudarem a narrativa. Varie escala, composição e superfície sem impor templates, cotas ou flutuação genérica. Preserve o repertório expressivo no renderer efetivamente usado.

Respeite o modo solicitado: se o pedido disser produção direta sem testes, não rode suítes de testes localmente ou no CI, prévias ou demonstrações. Registre o que não foi executado e preserve as suítes permanentes. A preparação necessária do render real continua: compilação/typecheck de produção, contratos, assets, fontes, integridade de voz e alinhamento; não prometa bypass desses gates. No modo normal, confira roteiro, recursos executáveis e layout antes da narração.

A produção na main está autorizada: acompanhe o vídeo real, corrija falhas preservando a explicação e retome pelo cache. Julgue ritmo percebido, movimento dos objetos, legendas, legibilidade e uso dos vazios no MP4 com áudio; um CI verde não aprova a linguagem visual. Dê atualizações claras no chat e continue até confirmar vídeo, título e descrição na pasta do Google Drive; disparar o render não conclui o pedido. Depois faça a capa final conforme as regras do canal e entregue-a na mesma pasta. Ao terminar, informe os links da entrega e eventuais limitações reais.`;
}
