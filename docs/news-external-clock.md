# Relógio externo de recuperação de notícias

Estado em 10/11/2026: implantado com credencial cadastrada pelo titular e disparo
natural observado às 15h41min06s de Fortaleza. O log da função registrou
`source=netlify_schedule`, `status=guard_recent` e `run_id=42877023766`: a consulta
autenticada reconheceu o vigia recente e evitou duplicação. A escrita de dispatch
com essa credencial ainda precisa de uma ocorrência sem vigia ativo/recente;
não confundir essa consulta bem-sucedida com publicação de notícia.

O vigia também reage à conclusão dos workflows do editor e do render na `main`,
inclusive quando um cron editorial atrasado termina sem produzir. Esse evento
confere todas as janelas ainda válidas, sem reinterpretar o cron antigo como uma
edição nova. O próprio vigia não está na lista de workflows observados; mantém
concorrência única, pausas entre tentativas, recibos e política de recuperação.
Essa recuperação por eventos reduz a dependência do cron, mas não substitui o
relógio externo quando não chega evento algum do GitHub.

Para volume e continuidade, a política autorizada posterior em 10/11 retira o
corte por atraso e o teto acumulado de tentativas das edições do dia. Cada vigia
entrega no máximo um editor, priorizando a edição com menos tentativas e depois
o horário mais antigo. Assim uma pauta que falha repetidamente não ocupa todas
as oportunidades das edições seguintes. As pausas, a apuração e os recibos
continuam obrigatórios. Uma rejeição material grava fontes em quarentena também
no cache do Actions; a próxima pesquisa exclui essas páginas em vez de repetir
o mesmo acontecimento rejeitado.

O Netlify já hospeda o painel `odinheiroexplica`. A função agendada `news-watchdog`
consulta o vigia da `main` e solicita sua execução quando não há execução ativa ou
iniciada nos últimos vinte minutos. O vigia existente decide quais episódios faltam,
recupera o render ou a publicação e mantém a política atual de tentativas. A função externa
não redige, não usa modelos, não envia vídeos e não recebe parâmetros públicos.

Agenda UTC `11,41 * * * *`. A janela válida é calculada a partir de
`config/news-autonomy.json`, em America/Fortaleza. Respostas de erro não permitem um
disparo; repositório e workflow são constantes, sem destino arbitrário. O estado
mais recente é registrado no Netlify Blobs `ode-news-clock/latest`, sem credenciais.

## Credencial e ativação

Criar uma credencial fine-grained própria para `Lucascristao/odinheiroexplica`,
com **Actions: read and write** e Metadata read obrigatório do GitHub. Selecionar
somente esse repositório. Não usar a credencial ampla do CLI nem conceder escrita
em código, administração, segredos, issues ou outros repositórios.

Guardar como `ODE_NEWS_TRIGGER_GITHUB_TOKEN` no projeto Netlify `odinheiroexplica`,
marcada como secreta, contexto production e escopo Functions. Não colocar no chat,
no Git ou em variável `VITE_*`. Depois publicar o código e gerar um deploy de produção
para aplicar a variável; previews não executam os agendamentos. Registrar a validade
da credencial e sua renovação antes de expirar.

Confirmar um disparo **natural** do Netlify e a execução GitHub `ODE watchdog | netlify`,
com `trigger_source=netlify` no recibo. Confirmar também que uma execução ativa/recente
é reconhecida. Só então declarar o relógio externo operacional.

## Evidência que motivou a mudança — 10/11/2026

Às 08h36 de Fortaleza, não havia editor nem JSON da edição das 08h. O commit remoto
era o mesmo local (`4c32736`) e os arquivos do workflow tinham o mesmo SHA. A recuperação
manual do vigia `42809182676` iniciou manhã e manhã-2 às 08h39. O render da manhã
`42810877532` publicou o vídeo `1ofBrOabvfc` às 09h26; a capa entrou depois pelo fluxo
`42817936852`. O vigia agendado `42816429007` apareceu às 09h31 e tentou recuperar manhã-2.

Isso comprova ausência/atraso dos gatilhos na janela, não uma causa interna específica
do GitHub. A documentação admite atrasos e descartes de eventos `schedule`; o status
público não registrava incidente ativo de Actions na consulta.

A revisão automática de segurança rejeitou extrair o token existente do CLI e copiá-lo
ao Netlify por falta de autorização explícita dessa transferência e do seu alcance.
A credencial foi posteriormente cadastrada diretamente pelo titular, sem extrair
a autenticação do CLI. Os gatilhos nativos continuam como proteção adicional,
sem promessa de pontualidade.
