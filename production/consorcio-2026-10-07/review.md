# Revisão e entrega · Consórcio · 7 de outubro de 2026

**Título:** Consórcio: por que pagar não garante levar o carro?  
**Capa:** PAGOU. E AGORA?  
**Pasta:** https://drive.google.com/drive/folders/17qR45AW8_eN1eP0aZkIP-0fVNeIjohZw

## Resultado e origem

MP4 real em 1920×1080, 30 fps, 12.617 frames e 7:00,57. SHA256: `60d65d7ff77932937550894fa1df13643567431f0b0a2eb62c2a05eb7e7df036`.
Render original: [37577381645](https://github.com/Lucascristao/odinheiroexplica/actions/runs/37577381645), commit `1dcfb0384cd4d70bb2be1c1ee597f4861dffdcc6`.
Retomada e entrega: [37581899656](https://github.com/Lucascristao/odinheiroexplica/actions/runs/37581899656), commit `c1e188d409a6351b0bcf074fa369851b3e56aca6`, concluída com sucesso. Nenhuma nova síntese ou render: mesmo hash de vídeo e mesmos WAVs.

A extração antiga comparava a duração do contêiner com a timeline e interrompeu a entrega por uma cauda AAC de 0,062666 s. A trilha de vídeo correspondia exatamente à timeline. O extrator agora usa o relógio da trilha de vídeo; extração e métricas auxiliares não bloqueiam um MP4 aprovado pelo QA. Falhas de integridade continuam bloqueantes. A retomada preserva a procedência do arquivo e registra o resultado da conferência.

## Melhorias comprovadas nesta produção

- Oito skills portáveis, pedido compartilhado dos botões diário/assunto e CLI documentada; autoria independente do fornecedor de IA, com ferramentas e permissões de execução.
- Duas artes HTML HyperFrames geraram três clipes reais, usados nas cenas 1, 2 e 9. Estados de carro/trava e fundo comum foram ligados aos eventos da timeline. Os hashes dos clipes foram conferidos.
- Nove cenas com Roberto/Charon, Gemini 3.8 Live, sessões isoladas e direção `explain` consistente. Transcrições de saída conservaram 100% dos tokens canônicos, sem diferenças.
- A equalização da trilha contínua reduziu a variação medida de energia da fala ativa de 2,596 dB nos WAVs para 0,0764 dB no master. Faixa real −18,007 a −17,931 dBFS. WAVs brutos preservados; não foi feita correção de pitch.
- MP4 final: −15,74 LUFS, pico verdadeiro −0,99 dBTP, LRA 2,8 LU. Nenhuma falha de integridade no QA.
- Fontes, pronúncia e layout final passaram. Cinco fontes, quatro publicadores, consulta à direita registrada; fonte normativa oficial capturada e usada na cena 3. Capítulos derivados dos tempos reais, uma lista de fontes e três hashtags no pacote de publicação.

## Inspeção visual e explicação

O agente principal inspecionou os contatos reais das cenas 1 e 2. A revisão paralela inspecionou os sete contatos das cenas 3 a 9 e oito quadros completos do MP4. O extrator produziu 243 quadros de prova e 841 amostras regionais. Os contatos selecionados estão em `evidence/`; o pacote completo está no Drive.

Não foram encontrados defeitos concretos de corte, colisão ou aritmética nos quadros inspecionados. O artigo 22, §1º aparece legível; sorteio/lance ficam separados. As contas R$100mil×20%=R$20mil, R$100mil+R$20mil=R$120mil e R$100mil−R$30mil=R$70mil estão corretas. Os exemplos identificam taxa total, hipótese sem reajuste, base mais administração e condições do lance. A chave e a barreira mantêm a contemplação como condição, sem prometer entrega automática.

As cenas 4–6 usam continuidade das mesmas três regiões para demonstrar taxa, soma de base/taxa e subtração do lance. A repetição 1/9 retorna à pergunta inicial e responde a ela; não motivou nova produção apenas por semelhança geométrica.

A capa completa foi gerada pela ferramenta nativa `image_gen` após a entrega do MP4. O JPEG conserva a composição gerada, com conversão de formato apenas: 1672×941, 414.140 bytes, sem marca, preço ou documento bancário falso. Prompt e origem estão versionados nesta pasta.

## Limites reais da revisão

A sessão informou que não suporta entrada de áudio ao receber o áudio extraído do MP4. Portanto **não houve escuta perceptiva completa**, aprovação de naturalidade/timbre ou reprodução audiovisual contínua pelo agente. Integridade, atividade sonora, fidelidade textual e energia foram medidas; não substituem escuta.

Há 51 de 79 âncoras visuais confirmadas e 28 estimadas; 10 dos 338 tempos de legenda continuam estimados. Três avisos estimados de registro vocal (emendas 1→2, 2→3 e 6→7) não comprovam mudança de identidade. Pausas entre cenas medidas: 0,547–0,647 s. O relatório de Stage aponta 21 intervalos declarados acima de 5 s; não mede sozinho a animação interna GSAP. Esses avisos não foram apresentados como sincronização comprovada, defeito audível ou motivo automático de refazer a produção.

Quadros amostrados não certificam cada frame intermediário nem a sincronização completa de legendas. Nenhum CTR, retenção ou equivalência entre modelos de autoria foi medido. Publicação no YouTube permanece manual.

## Arquivos e reprodução do fluxo

Pesquisa/storyboard: `research/consorcio-2026-10-07.md`. Projeto: `video/data/daily.json`. Prompt reutilizável: `docs/production-prompt.md`. Skills: `skills/ode-video/SKILL.md`.
Relatórios e recibos nesta pasta registram origem, hashes e limites. Derivados grandes e provas completas ficam nos artifacts e no Drive. A capa e este relatório seguem pelo workflow de suplemento para a mesma pasta.
