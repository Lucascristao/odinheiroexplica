# Storyboard e apuração: conta de luz com consumo baixo (08/10/2026)

**Estado:** pauta nova escolhida sob autorização expressa. Não substituir por pauta de 07/10. **Projeto:** `conta-luz-minimo-2026-10-08`.

## Decisão editorial

- **Pauta viral escolhida:** Conta de luz: por que vem cobrança mesmo sem gastar energia?
- **Capa:** `DESLIGOU. PAGOU.` Foto editorial de medidor residencial e disjuntor desligado com fatura ainda existente; preto/carvão, branco quente, amarelo #FFBD19. A imagem não deve fingir ser documento ou conta real.
- **Público concreto:** morador que deixou imóvel pouco utilizado, economizou muito ou conferiu consumo baixo e estranhou a conta; não presumir dados demográficos.
- **Crença:** pagar somente a energia medida implica fatura zero quando o medidor para.
- **Descoberta imediata:** baixo consumo pode gerar cobrança de disponibilidade da rede, cujo patamar depende da ligação; há exceções, especialmente Tarifa Social.
- **Hipótese testável:** abrir com a distinção entre consumo medido e mínimo faturável, demonstrada no medidor e na fatura, pode ajudar retenção inicial. Comparar 30 s, CTR e duração média com vídeos de mesmo formato, faixa de idade e origem; não atribuir causalidade.
- **Gancho de 0–5 s:** “Você desliga quase tudo. O consumo despenca. Mas a conta continua chegando. Por quê?”
- **Gatilho:** aversão a cobrança inesperada, sem afirmar fraude ou cobrança universal.
- **Fonte primária:** ANEEL, REN 1.000/2021, art. 291 e informações oficiais de Tarifa Social; regra 30/50/100 kWh-equivalentes e seus casos de aplicação/exceção.
- **Contraponto:** Gazeta do Povo, 22/05/2025, editorial “Populismo bancado pela classe média” consultado apenas para a discussão distributiva da Tarifa Social, não como fonte normativa nem como consenso; cruzar com o esclarecimento da ANEEL de que a CDE tem fontes de custeio e com as regras atuais. Evitar importar projeções políticas antigas como valores atuais.
- **Atualidade:** consulta em 08/10/2026. Não inventar preço nacional por kWh ou percentuais de beneficiários atuais.
- **Limites:** grupo B residencial comum, custos e tributos variam; cadastro em Tarifa Social altera o piso; geração distribuída (solar) tem regras próprias; exemplos monetários apenas hipotéticos.

## Storyboard executável, antes do JSON

| Cena | Pergunta, protagonista e prova | Relação/transformação na fala | Saída e geometria |
| --- | --- | --- | --- |
| 01 | Por que pagar sem uso? Medidor grande domina o lado esquerdo, fatura simbólica à direita, nenhum valor fictício no documento. | Medidor perde barras de consumo e uma camada “disponibilidade” continua ativa; corte para distinguir “mediu” e “faturou”; câmera acompanha o medidor e revela a conta. Primeira resposta aparece logo após o gancho, antes da apresentação de Roberto. | Medidor/conta ficam inteiros; não usar o comprovante do episódio de 07/10 nem o celular do Pix. |
| 02 | O que significa disponibilidade? Transformador/poste/rede de cabos abastecendo uma casa; conexão desenhada da rede até a casa, não textos apenas. | Rede permanece operacional enquanto o indicador de consumo cai; rótulo “rede pronta para uso” surge. Câmera percorre rede > casa; sem afirmar que a taxa é valor fixo universal. | Mudança física: conexão ativa mesmo quando quase não há consumo. |
| 03 | Quanto é o patamar? Três padrões de entrada grandes, e números protagonistas `30 / 50 / 100 kWh`. | Revelar 30 para monofásico ou bifásico 2 condutores, 50 para bifásico 3 condutores e 100 para trifásico; deixar claro que são equivalentes para calcular piso, não energia necessariamente usada. Reframing por grupo. | Números inteiros; sem porcentagem ou tarifa fictícia disfarçada. |
| 04 | Como o cálculo funciona? Contador de 8 kWh e uma base de 30 kWh; valor unitário fictício R$ 0,80/kWh. | Etiqueta “EXEMPLO HIPOTÉTICO”: 30 × R$ 0,80 = R$ 24 para parcela ilustrativa; não somar como consumo adicional. Mostrar medição 8 e piso 30, operação com participantes, total e ressalva dos demais itens. | Câmera move do medidor ao cálculo; não exibir “R$ 24” como cotação real. |
| 05 | Quem pode não pagar essa parcela? Tarifa Social em um documento original da ANEEL; destaque preciso de `80 kWh`. | Primeira faixa grátis na componente energia, quando há direito, mesmo em trifásico; demais itens não necessariamente desaparecem. Documento entra quando citado. | Nota de limite clara; conferir captura autêntica e texto. |
| 06 | Por que a fatura ainda pode existir? Fatura esquemática completa com parcelas separadas, CIP/tributos sem números. | A parcela energia pode ser abatida e iluminação pública municipal continuar (se houver); ICMS varia pela situação tributária. Separação visual das linhas, sem simular documento real. | Não dizer que todo município cobra CIP nem que há taxa fixa igual em todo Brasil. |
| 07 | Como conferir a própria cobrança? Fatura genérica ampliada em sequência: consumo medido, tipo de ligação, piso, Tarifa Social, CIP e canal da distribuidora. | Zoom documental progressivo em cada campo com grifo; concluir respondendo por que a cobrança aparece, com condições e exceções. | Saída fecha no campo “confira sua fatura”, sem promessa de cancelamento ou devolução. |

## Fonte rastreável

1. ANEEL, Resolução Normativa nº 1.000/2021, art. 291: https://www2.aneel.gov.br/cedoc/ren20211000.pdf (consulta 08/10/2026). A norma determina equivalentes de 30/50/100 kWh conforme ligação e prevê condições de não aplicação.
2. ANEEL, Tarifa Social: https://www.gov.br/aneel/pt-br/assuntos/tarifas/tarifa-social (consulta 08/10/2026). Desde julho de 2025, primeiros 80 kWh com desconto integral para beneficiários e possibilidade de outras cobranças.
3. ANEEL, Micro e Minigeração Distribuída: https://www.gov.br/aneel/pt-br/assuntos/geracao-distribuida/ (consulta 08/10/2026). Custo de disponibilidade do grupo B inclusive em sistemas com injeção superior ao consumo; não generalizar sem condições.
4. ANEEL, Iluminação Pública: https://www.gov.br/aneel/pt-br/assuntos/iluminacao-publica (consulta 08/10/2026). Município ou Distrito Federal define a contribuição local.
5. ANEEL, Custo da energia: https://www.gov.br/aneel/pt-br/assuntos/tarifas/entenda-a-tarifa/custo-da-energia-que-chega-aos-consumidores (consulta 08/10/2026). Energia, transporte, encargos e tributos.
6. Gazeta do Povo, editorial de 22/05/2025: https://www.gazetadopovo.com.br/opiniao/editoriais/populismo-bancado-pela-classe-media/ (consulta 08/10/2026). Contraponto sobre fonte de financiamento da gratuidade, sem atribuir ao editorial força normativa.

## Contrato de observação

A revisão dos artifacts deve conferir início e fim de cada beat, intervalos sem atuação, fonte dos alinhamentos (confirmado/estimado), gráfico ocupando a área principal, leitura no celular, instante da primeira resposta e áudio real completo. Um efeito declarado não é prova de execução. Não aprovar nem anunciar Drive concluído sem MP4, metadados, capa e revisão observados.
