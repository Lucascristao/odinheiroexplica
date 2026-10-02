export function productionChatRequest(request: string): string {
  return `${request}

Use o sistema https://github.com/Lucascristao/odinheiroexplica e siga as regras de AGENTS.md, prompts/daily-editorial.md e docs/editorial-motion-library.md.

DIRETRIZES VISUAIS OBRIGATÓRIAS (Padrão de Dinamismo):
1. RITMO E ILUSTRAÇÃO CONTÍNUA (Regra dos 4 segundos):
   - A narração deve ser ilustrada o tempo todo. Cada nova afirmação, dado ou virada de raciocínio da fala exige um evento visual correspondente.
   - NUNCA deixe a tela estática ou com a mesma lista/gráfico parado por mais de 4 a 5 segundos enquanto o narrador fala de outros tópicos. Divida a cena em microcenas e beats visuais ativos.

2. ELEMENTOS VISUAIS E SVGs GRANDES:
   - Os elementos gráficos e ilustrações em SVG devem ser GRANDES, centrais e protagonistas (250px a 500px de destaque), nunca ícones pequenos e tímidos perdidos na tela.
   - Aplique animações de traço (trace), fluxo ativo (flow) e sustentação viva (breathe, float, pulse) para manter a tela em movimento orgânico durante a explicação.

3. TIPOGRAFIA CINÉTICA E NÚMEROS GIGANTES:
   - Destaques numéricos, valores em dinheiro e porcentagens devem ser GIGANTES e impactantes, usando kinetic_type e count em amarelo #FFBD19 sobre a base escura.

4. CÂMERA ATIVA E REENQUADRAMENTO:
   - Planeje movimento de câmera com propósito narrativo: push-in para revelar detalhes e gerar tensão, pan para comparações e reframe para acompanhar o novo foco da narração. Evite câmeras totalmente paradas o vídeo inteiro.

5. IDENTIDADE VOCAL E ENTREGA:
   - Narrador padrão: Roberto com voz Charon (Gemini Live). Use Luana/Autonoe apenas se a pauta for especificamente voltada ao público feminino.
   - Entregue o vídeo renderizado, título e descrição completa na pasta do Google Drive.

6. CAPA FINAL (THUMBNAIL):
   - Ao concluir a entrega do vídeo no Drive, gere a thumbnail final 16:9 de alta conversão: limpa, minimalista, com texto de 2 a 4 palavras, sem poluição visual ou erros de texto, e salve-a na mesma pasta do Drive.`;
}

