# Embalagem para YouTube - títulos e descrições

Estas regras valem para toda nova produção do O Dinheiro Explica. O objetivo é aumentar clareza, descoberta e vontade de clicar sem transformar a embalagem em clickbait.

## Título: assunto primeiro, consequência depois

O título deve traduzir regra, imposto, economia ou tecnologia para uma consequência concreta para quem assiste.

Regras:
- coloque o assunto ou palavra-chave principal nas primeiras 3 a 5 palavras sempre que isso soar natural;
- prefira títulos que continuem compreensíveis quando o YouTube cortar o final no celular;
- use como referência editorial cerca de 45 a 65 caracteres; o limite técnico continua em 100;
- pense internamente em uma formulação de busca e outra de curiosidade, mas publique apenas uma opção;
- quando funcionar, use a estrutura `Fato/tema: consequência ou dúvida`;
- depois de nomear o assunto, dê motivo concreto para clicar: dinheiro, custo, prazo, limite, segurança, bloqueio, imposto, risco ou efeito prático, somente quando sustentado pela pauta;
- não abra com número de norma, nome burocrático ou expressão administrativa se o público pode entender primeiro a consequência;
- evite começos genéricos como "Entenda", "Saiba" ou "Veja" quando o próprio assunto puder abrir o título;
- não afirme ganho, prejuízo, risco ou urgência que o roteiro não demonstra.

Exemplo de lógica:
- fraco: `Entenda a nova regulamentação do Pix por aproximação`
- melhor: `Pix por aproximação sem teto: o que muda acima de R$ 500?`

A fórmula é uma ferramenta, não um template obrigatório. Não force dois-pontos quando outro título for mais claro.

## Sinergia título + thumbnail

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
