# Direção editorial com continuidade

Regra geral para todos os próximos vídeos: uma cena mantém objetos e relações; cada evento da fala revela, destaca, atualiza, reposiciona ou retira esses objetos. Uma frase nova não exige uma cartela nova.

## Contrato

Cenas com visual.beats precisam de visual.stage. O validador de produção roda antes da síntese paga. Projetos antigos sem beats continuam no renderer legado.

stage.elements contém objetos com id estável, kind (step, label, metric, note ou photo), label, detail/value opcionais, x/y/width/height em porcentagem da área segura. Elementos inicialmente ocultos usam initially_visible:false. As regiões não podem se sobrepor nem sair da área segura, mesmo antes de aparecer. Composição por pauta: não copiar a geometria do MED para outros assuntos.

stage.connections liga IDs from/to; a conexão acompanha a geometria e o destaque da fala. Não desenhar ligações causais apenas por decoração.

Informações que pertencem a um momento futuro da explicação começam com `initially_visible:false` e só aparecem por `action:reveal` ou `reveal_ids` quando a fala chega a elas. Não mostrar o próximo texto, número ou dado cortado na borda como antecipação. O estado inicial e cada movimento de câmera devem preservar inteiros o objeto em foco, seu rótulo, dado e unidade; revisar os quadros intermediários, além do início e do fim do movimento. A câmera acompanha informação já apresentada e para para leitura. Esta regra vale para todos os vídeos, sem impor geometria ou percurso fixos.

Cada beat precisa de:
- anchor literal, único, na ordem da narração;
- target_id existente;
- action: focus, reveal, update ou retire;
- prominence: support, contextual (padrão) ou takeover;
- headline para intenção editorial; só update troca o label do objeto;
- reveal_ids e retire_ids opcionais para controlar anotações já posicionadas;
- moves opcional: lista de {id,x,y}. O objeto conserva seu tamanho e identidade, movendo-se por frame. O percurso deve ter área livre;
- sound: none por padrão; som apenas quando traz significado.

Takeover exige takeover_reason e não pode ocorrer em eventos consecutivos. No palco persistente, takeover concentra a atenção atenuando o contexto: não usa cartela opaca que apaga os objetos. Se uma mudança real de assunto exige novo plano, crie outra cena narrativa.

## Autoria

1. Definir o que o espectador deve compreender.
2. Escolher objetos concretos ou relações que mostrem isso.
3. Planejar estado inicial, mudanças e conclusão.
4. Reservar regiões para texto complementar antes de animar.
5. Escrever âncoras que acionem cada mudança no momento da fala.
6. Reduzir texto, preservar tempo de leitura, remover efeitos sem função.
7. Rever se a composição nasceu da pauta ou foi copiada do último vídeo.

Repetir o tratamento ao desenvolver o mesmo fluxo é permitido e desejável. Variedade deve existir entre necessidades narrativas e pautas, não por sorteio de efeitos a cada frase. Não impor animação de entrada/desenvolvimento/saída em toda frase. Uma pausa legível é válida.

Metric mostra o dado final com sua unidade; não conta automaticamente prazos desde zero. Nunca converter ausência de dado em barra percentual. Comparação precisa de dois objetos explicitamente nomeados; não presumir ANTES/AGORA. Lista/processo requer itens explícitos, não separação automática por pontuação.

Fotos usam asset_id preparado no pipeline. photo_style:clean mantém transparência; paper usa suporte claro com borda irregular. Papel é uma opção, não padrão obrigatório. Não sacrificar leitura para colocar texto atrás de uma imagem. Documentos e capturas podem ser preparados como imagens e posicionados em regiões próprias, com crédito e contexto.

A fonte Inter é distribuída com sua licença e carregada antes de medir texto. O renderer reduz a fonte dentro de limite legível e falha se ainda não couber; nesse caso ampliar a região ou reescrever. Nada de letter-spacing negativo para espremer informação.

## Pesquisa aplicada e limites

- Remotion: animação derivada do frame, para reprodução e render paralelo consistentes. Aplicado ao estado persistente, conexões, entrada e reposicionamento. Fonte: https://www.remotion.dev/docs/animating-properties
- Remotion Bits: stagger e mudanças coordenadas ajudam a organizar elementos, mas não decidem o significado da cena. Mantemos primitivas próprias pequenas e acionadas por tempos estimados das âncoras da narração, sem instalar um catálogo de efeitos. Esses tempos não são bookmarks emitidos pelo TTS. Fonte: https://remotion-bits.dev/docs/reference/staggered-motion/
- Curvable: determinismo e componentes de texto são úteis; os templates de lançamento SaaS não são a composição editorial do canal. Fonte: https://github.com/Curvable/motion
- Edição: match cuts e continuidade de atenção inspiram manter o mesmo objeto ao mudar seu papel. J/L cuts separam o momento do corte de imagem e do áudio; são uma evolução futura que exige modelo de sobreposição de cenas, não aplicada implicitamente ao áudio atual. Fonte: https://www.adobe.com/in/creativecloud/video/discover/match-cut.html e https://helpx.adobe.com/sg/premiere/desktop/edit-projects/trim-clips/perform-j-cuts-and-l-cuts.html

Vídeo moderno também pode usar B-roll, captura de documentos e pontes sonoras, quando houver material adequado. Não fabricar cenas factuais nem acrescentar clipes genéricos só para preencher tempo. B-roll em movimento e J/L cuts não foram implementados nesta etapa. O ganho aplicado agora é a continuidade de objetos e informação, com composição livre por pauta.

