# Revisão visual para produção direta — 07/10/2026

Pedido: refazer o episódio e corrigir o motor para os próximos vídeos, sem suítes de testes ou prévias de demonstração.

Problema observado nos prints de 0:30 e 1:16: arte encaixada em região baixa, faixa fixa de rótulo, aviso técnico desnecessário, tipografia pequena e terço inferior reservado sem necessidade. A nova composição libera o quadro para a explicação. A narração, a voz e os fatos permanecem os mesmos.

| Cena | Protagonista e relação | Transformação e enquadramento |
|---|---|---|
| 01 | Comprovante e pedido recusado | Arte ampla abaixo da pergunta grande; pagamento, recusa, critérios e histórico mudam partes da ilustração nas falas correspondentes. |
| 02 | Arquivo com três informações distintas | Arquivo grande à esquerda e conceito grande à direita; cada documento ganha presença no momento certo, a lupa percorre a informação consultada. |
| 03 | Situação de setembro versus outubro | Calendários grandes com meses legíveis; entrada do pagamento, contraste do retrato antigo e da posição posterior. Exemplo hipotético permanece identificado. |
| 04 | Trecho original do Banco Central | Prova ampliada, contexto preservado e consequência curta em texto grande; aproximações dirigidas sem fabricar recorte ou conteúdo. |
| 05a | Instituição e capacidade de pagamento | Banco e carteira grandes lado a lado; carteira entra quando a fala menciona renda. |
| 05 | Conta ilustrativa de R$ 800 + R$ 700 = R$ 1.500 | Valores grandes entram conforme a narração; a operação preserva os três participantes, renda e limites da hipótese. |
| 06 | Relatório e percurso de correção | Documento grande e etapas laterais com ícones maiores; banco, protocolo, ouvidoria e BC se atualizam na fala. |
| 07 | Arquivo e conclusão | Arte grande e resposta em texto amplo; destaque do mês e consulta final. |

Motor: `show_label: false` mantém o metadado sem reservar pixels; rótulos visíveis usam altura medida; relatório registra o envelope real de SVG/clipe depois de contain e câmera. `visual_role` identifica protagonista e apoio. As regras canônicas agora orientam os próximos episódios a usar arte grande e informação legível sem reservar faixa para legendas. Diagnóstico de escala é orientação editorial e não um novo teste ou render de demonstração.

Verificação: apenas contratos, compilação e preparação necessária do render real. Suítes locais e job de testes do CI não serão executados neste push `[production direct]`. A avaliação final usa os quadros e o MP4 da produção real, sem declarar dinamismo apenas pelo nome dos tratamentos.
