export function productionChatRequest(request: string): string {
  return `${request}

Use o sistema https://github.com/Lucascristao/odinheiroexplica e leia as instruções atuais de AGENTS.md e prompts/daily-editorial.md. Crie direção de voz, câmera e motion graphics própria para esta pauta, preservando o tema escolhido. Valide o roteiro, os recursos realmente executáveis e o layout antes da narração. A produção na main está autorizada: acompanhe as verificações e o vídeo real, corrija falhas preservando a explicação e retome pelo cache. Dê atualizações claras no chat e continue até confirmar vídeo, título e descrição na pasta do Google Drive; disparar o render não conclui o pedido. Depois faça a capa final conforme as regras do canal e entregue-a na mesma pasta. Ao terminar, informe os links da entrega e eventuais limitações reais.`;
}
