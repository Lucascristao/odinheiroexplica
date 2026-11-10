# Fallback gratuito de texto

Autorizado pelo titular em 10/11/2026: Groq continua principal, com GPT-OSS 20B
como reserva interna e OpenRouter como provedor externo quando há erro de
conexão, cota ou indisponibilidade. Um parecer factual negativo não aciona essa
cascata: o motor corrige ou pesquisa outro acontecimento.

`worker/news_free_fallback.py` fixa o endpoint oficial e variantes `:free`, com
preço máximo zero para entrada/saída, sem plugins ou modelos pagos. Preserva
pedidos JSON/schema e registra o modelo efetivamente retornado. Se os gratuitos
também estiverem indisponíveis, a recuperação volta após a pausa; não há cobrança
automática nem promessa de disponibilidade ilimitada.

O primeiro teste de conexão com `openrouter/free` retornou Liquid 1.7B e confirmou
a chave/JSON/custo zero. Para o trabalho editorial, o catálogo real de 10/11 foi
consultado e a seleção passou a priorizar `nvidia/nemotron-3.5-super-vl:free`, com
`xingchen-agi/xing4.0-29b-a4b:free` de reserva; ambos anunciam texto e saída
estruturada. A lista fixa evita escolher aleatoriamente um modelo pequeno.

Cadastrar `OPENROUTER_API_KEY` em GitHub Actions → repository secrets, somente
no backend. O editor e a avaliação leem esse secret; a voz continua exclusivamente
Gemini Live/Charon, e a visão da capa continua Groq opcional.

`news-provider-availability.yml` confere uma chamada real com JSON schema em
artefato, sem produzir notícia, voz, render ou publicação. Sucesso offline,
configuração do secret e API real aprovada são estados distintos.

Fontes oficiais verificadas em 10/11/2026:
- https://openrouter.ai/docs/guides/routing/routers/free-router
- https://openrouter.ai/docs/guides/routing/model-variants/free
- https://openrouter.ai/docs/api/reference/limits

Os modelos gratuitos têm cotas próprias e disponibilidade variável. Somente
variantes `:free` da lista fixa entram nesta integração; nomes configurados para modelos pagos
não alteram o roteador fixo do código.
