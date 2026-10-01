# Biblioteca de movimento editorial

> Para a produção atual, siga primeiro [editorial-continuity.md](editorial-continuity.md). Os tratamentos antigos abaixo são recursos legados; não substituem o contrato de palco persistente.

Esta biblioteca existe para ampliar a linguagem do canal, não para criar um novo template fixo.

Ela foi desenhada a partir de três referências técnicas estudadas em setembro de 2026:
- composição por camadas/máscaras em React + Remotion, com texto atrás de fotografia recortada;
- Curvable Motion, especialmente seus princípios de animação determinística por frame, cascade de palavras, sweep de texto, bloom e paleta derivada;
- Remotion Bits, especialmente AnimatedText, AnimatedCounter, StaggeredMotion, Ken Burns, barras animadas e reframing.

A implementação do projeto é própria e usa apenas os conceitos úteis para o canal.

## Capacidades atuais

### Operações do palco persistente

Para produções novas, a matriz implementada está em `visualCapabilities`, no módulo `src/lib/editorial-layout.ts`. As operações têm dados próprios em `beat.operation`; escolher apenas um nome em `treatment` não constrói uma demonstração.

| Operação | Dados e função |
|---|---|
| `equation` | `input_ids`, `operator`, `result_id`: liga valores declarados aos operadores; os números e a conta são conferidos em `editorial.explanation`. |
| `compare` | `element_ids`: destaca os participantes da comparação, sem escolher automaticamente um vencedor. |
| `stack` | `element_ids`: conecta itens em ordem vertical; reserve o corredor lateral. |
| `meter` | `value`, `min`, `max`, `unit`: representa uma escala explícita, sem limitar silenciosamente um valor inválido. |
| `signal` | `status`, `message`: revela uma condição textual, com seu significado declarado. |

Conexões reservam espaço para suas legendas e acompanham a geometria dos objetos. `semantic: transfer` precisa representar uma transferência real; sem `token_label` explícito, o token é neutro. O motor não infere dinheiro por palavras da narração. Preserve as relações e deixe o conteúdo futuro oculto até o beat correspondente.

A composição compartilhada usa a fonte de produção no Chromium e verifica estados de entrada, movimento, atualização e câmera. Falta de espaço produz diagnóstico antes da voz; aumentar a área, reorganizar blocos ou dividir a explicação é uma decisão editorial. Não reduzir indefinidamente a fonte nem esconder palavras.

O Actions executa uma verificação antes da narração e outra com o relógio do áudio real, salvando quadros e relatórios. Textos em imagens documentais ainda exigem conferência visual: geometria válida não comprova legibilidade raster.

### word cascade

Aplicado dentro de kinetic_type. Palavras não aparecem como um bloco único: entram em sequência, com deslocamento, blur e mudança de cor. A sequência precisa caber no intervalo real do beat.

### animated number

Aplicado em valores numéricos. O número progride durante a explicação e preserva prefixo, sufixo e separador decimal quando possível.

Use quando o número for informação real. Não anime números apenas por decoração.

### masked emphasis

Treatment: masked_emphasis.

Uma faixa de destaque percorre a frase sem trocar a composição inteira. Use para uma conclusão, ressalva ou contraste curto. Não repetir várias vezes na mesma cena e não usar em texto longo.

### depth photo

Treatment: depth_photo com medium: photo_cutout.

A fotografia recortada ocupa uma camada entre texto de fundo e informação de primeiro plano. O objeto precisa ocultar parte do texto ou interagir espacialmente com a composição; caso contrário, use a composição fotográfica comum.

É a forma preferencial quando uma foto tem papel narrativo forte.

### bloom

Transition: bloom.

Expansão curta de luz/cor usada como revelação ou mudança de estado. É pontual, não é fundo contínuo. Não usar em toda transição.

## Princípios

- toda animação é determinística por frame;
- o bookmark do TTS define a entrada do beat e o próximo bookmark define seu intervalo útil;
- cada beat continua tendo entrada, desenvolvimento e conclusão;
- movimento estrutural vale mais que movimento decorativo;
- fotografia, texto, número e diagrama podem ocupar camadas diferentes;
- profundidade não significa 3D: z-index, recorte, escala, máscara e parallax 2D são suficientes;
- não transformar os recursos em catálogo obrigatório;
- no máximo um efeito de destaque especial por trecho curto;
- o vídeo deve parecer editado para a história atual, não uma demonstração de biblioteca.

## Recursos que não entram no padrão

- cenas 3D;
- cubos, carrosséis 3D e UI inclinada apenas por estética;
- partículas decorativas;
- fundos WebGL pesados;
- confete, Matrix e efeitos de demo;
- gradiente ornamental permanente.

Esses recursos só podem ser considerados se tiverem função editorial clara e passarem por revisão específica.
