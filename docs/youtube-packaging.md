# Embalagem para YouTube - títulos e descrições

Estas regras valem para toda nova produção do O Dinheiro Explica. O objetivo é aumentar clareza, descoberta e vontade de clicar sem transformar a embalagem em clickbait.

Toda embalagem nova registra suas provas em `editorial.learning_strategy`, conforme [aprendizado por publicação](editorial-learning.md). Título/capa devem corresponder a claims verificados e às unidades que os explicam, com trechos literais de entrega e condições. Resultado quantitativo geral não pode nascer só de um exemplo hipotético. Mudança de embalagem exige renovar a revisão semântica do projeto com estratégia.

## Engenharia de Título Viral: Curiosidade, Dor e Gatilhos Mentais

O título não pode parecer um artigo acadêmico ou relatório de banco. Ninguém clica em "Marcação a mercado", "Juro real recorde", "Subvenção" ou "Spread bancário". O título deve explorar a psicologia do espectador no YouTube:

1. **Gatilhos Psicológicos de Alto CTR**:
   - **Aversão à perda (Medo de perder dinheiro)**: O ser humano tem o dobro de medo de perder o que tem do que vontade de ganhar. (Ex.: *Renda fixa dando prejuízo?*, *O erro que está comendo o saldo*, *O banco pode tirar o seu dinheiro?*).
   - **Curiosidade oculta / Segredo bancário**: O que não contam ou a regra escondida. (Ex.: *O que o banco nunca te conta sobre...*, *A trava oculta no seu benefício*).
   - **Contraintuitivo / Quebra de crença**: Chocar uma certeza popular. (Ex.: *Investimento seguro com saldo negativo?*, *Por que guardar na poupança te faz perder poder de compra*).
   - **Alerta de urgência no bolso**: Mudança em regras diárias (Pix, compras, demissão, FGTS, taxas).

2. **Regras de Ouro**:
   - **Zero jargão**: elimine termos técnicos do título. O roteiro pode e deve explicar o conceito com rigor, mas o título tem que ser 100% inteligível para qualquer pessoa no ônibus ou na fila do pão;
   - coloque o gancho principal nas primeiras 4 a 6 palavras (visível no feed do celular sem truncar);
   - use como referência editorial cerca de 45 a 65 caracteres;
   - evite começos mornos como "Entenda", "Saiba como", "Análise de";
   - nunca use clickbait enganoso: todo choque ou dúvida do título deve ser rigorosamente explicado e comprovado no vídeo.

### Exemplos de Transformação: Burocrático vs Viral
- ❌ **Burocrático**: `Tesouro IPCA+ com Juro Real Recorde: Oportunidade ou Armadilha da Marcação a Mercado?`
- ✅ **Viral**: `Renda fixa dando prejuízo? O erro que faz muita gente perder dinheiro`
- ❌ **Burocrático**: `Pix Automático e Resolução do Bacen: Análise de Débito em Conta`
- ✅ **Viral**: `O Pix vai tirar dinheiro da sua conta sozinho? A nova regra que assusta`
- ❌ **Burocrático**: `Regulamentação do Saque-Aniversário do FGTS em Caso de Rescisão`
- ✅ **Viral**: `Demitido e sem FGTS: a trava silenciosa que pegou milhões de surpresa`

## Situação reconhecível e descoberta

Antes de fechar a embalagem, identifique a crença inicial, o fato que a contraria, a consequência concreta no bolso e a demonstração que resolve a dúvida. Evite títulos com cara de aviso de serviço ou tutorial genérico; o conflito precisa existir na apuração, não ser acrescentado por palavras alarmistas.

Referência aprovada: "Supermercado: o aumento de preço que você não vê" + "CADÊ O RESTO?". A promessa é descobrir como a mesma etiqueta pode comprar menos produto. O exemplo orienta o critério de qualidade; não é fórmula de título nem autorização para repetir a pauta.

Caso real, hipótese, possibilidade de repasse e risco têm graus diferentes de certeza. Preserve essa diferença desde o título. Não usar valor ilustrativo como estatística, sugerir fraude sem prova ou garantir desempenho de cliques.

## Complemento visual

Título e thumbnail são uma única promessa, mas não repetem a mesma frase.

- o título identifica o assunto e a consequência/dúvida;
- a thumbnail transforma a tensão em imagem e, quando houver texto, usa preferencialmente 2 a 4 palavras;
- se a thumbnail apenas repetir palavras do título, reescreva uma das duas;
- a thumbnail não precisa explicar o assunto inteiro: ela precisa complementar o título sem criar outra promessa;
- preserve precisão factual e o DNA descrito em `docs/thumbnail-identity.md`.

## Descrição: estrutura de leitura rápida

`publication.description` contém somente o corpo editorial da descrição. Não inclua capítulos, fontes, créditos visuais, pergunta de comentários ou hashtags nesse campo; o pipeline monta essas partes uma única vez.

O corpo deve ter:

1. Gancho inicial
   - 2 a 3 frases curtas;
   - a palavra-chave principal aparece naturalmente logo no início;
   - diga o que mudou, qual pergunta o vídeo responde e o que a pessoa vai entender.

2. Tópicos rápidos
   - 3 ou 4 bullets;
   - cada bullet descreve uma resposta concreta entregue pelo vídeo;
   - use linguagem humana, não uma lista de palavras-chave.

Formato esperado:

```text
Pix por aproximação mudou: o teto específico de R$ 500 saiu, mas os limites da conta continuam valendo.
Neste vídeo, você entende o que realmente mudou e quando um pagamento maior pode passar.

- O que acabou no limite por aproximação
- Qual limite passa a valer
- Como funcionam redução e aumento no aplicativo
- Quais cuidados continuam importantes
```

## Campos de publicação

Além de `publication.description`, toda nova produção deve preencher:

- `publication.engagement_question`: uma pergunta simples, diretamente ligada ao vídeo, para comentários;
- `publication.hashtags`: exatamente 3 hashtags específicas e legíveis, sem espaços;
- `publication.seo.primary_keyword`: assunto principal que também orienta o começo do título e do gancho;
- `publication.seo.secondary_keywords`: apenas termos realmente relacionados.

O pipeline acrescenta automaticamente, nesta ordem quando houver conteúdo:
1. corpo editorial;
2. capítulos calculados pelo tempo real do vídeo;
3. uma única seção `FONTES`, com títulos consolidados e sem links;
4. créditos visuais necessários;
5. pergunta para comentários;
6. 3 hashtags.

## Capítulos

Os capítulos vêm do tempo real do render, nunca de minutagem inventada no roteiro. O primeiro precisa começar em `0:00`. O pipeline só publica capítulos quando o conjunto atende às regras técnicas já implementadas.

## Fontes

A descrição pública usa uma única lista de fontes, sem URLs. Não repetir referências dentro de `publication.description`. URLs continuam nos metadados internos do projeto.

## Revisão antes de aprovar

Antes do TTS, confira:
- o assunto aparece cedo no título;
- a consequência ou dúvida é concreta;
- título e thumbnail se complementam;
- o gancho da descrição contém a palavra-chave principal;
- há 3 ou 4 bullets úteis;
- não existem fontes, capítulos ou hashtags duplicados no corpo;
- a pergunta de comentários é natural;
- existem exatamente 3 hashtags;
- toda promessa do título, thumbnail e descrição é entregue pelo roteiro.
