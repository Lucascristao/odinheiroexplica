# Biblioteca de movimento editorial

> Para a produção atual, siga primeiro [editorial-continuity.md](editorial-continuity.md). Os tratamentos antigos abaixo são recursos legados; não substituem o contrato de palco persistente.

Esta biblioteca existe para ampliar a linguagem do canal, não para criar um novo template fixo.

Ela foi desenhada a partir de três referências técnicas estudadas em setembro de 2026:
- composição por camadas/máscaras em React + Remotion, com texto atrás de fotografia recortada;
- Curvable Motion, especialmente seus princípios de animação determinística por frame, cascade de palavras, sweep de texto, bloom e paleta derivada;
- Remotion Bits, especialmente AnimatedText, AnimatedCounter, StaggeredMotion, Ken Burns, barras animadas e reframing.

A implementação do projeto é própria e usa apenas os conceitos úteis para o canal.

## Capacidades atuais

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
