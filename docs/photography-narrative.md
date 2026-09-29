# Fotografia narrativa

## Direção

O fluxo não usa 3D como padrão. A linguagem visual combina motion graphics 2D, tipografia, diagramas, números, ícones e fotografia recortada.

Fotografia só entra quando representa algo mencionado ou necessário para entender a fala. Nunca use foto genérica apenas como fundo decorativo.

## Regras

- priorizar photo_cutout: sujeito recortado e integrado à composição;
- a foto também precisa ter entrada, desenvolvimento e conclusão durante o beat;
- para assuntos brasileiros, priorizar imagem feita no Brasil ou elemento visual inequivocamente brasileiro quando o contexto geográfico importar;
- imagem global ou neutra só deve representar gesto universal, sem sugerir que ambiente, moeda, banco ou serviço estrangeiro seja brasileiro;
- Google Imagens pode servir para descoberta, nunca como comprovação de licença;
- o arquivo usado precisa ter página de origem rastreável e licença compatível;
- priorizar Wikimedia Commons, bancos gratuitos com uso comercial permitido e acervos com licença explícita;
- registrar origem, URL da imagem, licença, atribuição quando necessária e papel narrativo em visual_assets;
- não usar fotografia de autoridade como atalho visual para uma regra quando a pessoa não for essencial à explicação;
- não usar uma marca bancária específica para representar o sistema inteiro sem necessidade;
- se não houver fotografia adequada e licenciável, usar motion graphic.

## VideoProject

Em visual.beats, usar:

- medium: photo_cutout
- asset_id: ID existente em visual_assets

O pipeline baixa a imagem escolhida, remove o fundo localmente e entrega um PNG transparente ao Remotion.

Tipos de recurso:
- photo_cutout
- photo
- graphic

Cada visual_asset registra:
- subject
- narrative_role
- country_context
- source_page_url
- image_url
- license
- attribution
- needs_cutout
