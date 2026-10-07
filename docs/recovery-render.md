# Retomar somente a entrega de um render aprovado

Se o MP4 e `Verify delivery before Drive` terminaram com sucesso, mas uma etapa posterior falhou, `resume-delivery.yml` aproveita o vídeo codificado e os áudios originais. Esse caminho não chama Gemini, não prepara novas animações e não renderiza novamente.

```sh
gh workflow run resume-delivery.yml --ref main -f source_run_id=ID_DO_RUN_ORIGINAL
```

A retomada exige um artifact `daily-production-review` ativo da última tentativa do workflow `render-daily.yml` na `main` do mesmo repositório. A origem precisa registrar sucesso do render, QA e upload do artifact. Forks, execuções incompletas, artifacts ambíguos, projetos alterados, hashes divergentes e arquivos fora da árvore autorizada são recusados antes da restauração.

O projeto atual é comparado, após normalização, com o projeto do commit original, o JSON editorial do artifact e seu projeto gerado. A comparação ignora apenas `captured_at` nos recortes documentais e o caminho automático de captura quando ausente na fonte e exatamente igual ao caminho produzido pelo capturador; textos, fontes, caminhos declarados e demais campos editoriais continuam obrigatoriamente iguais. O Git também confere que componentes, fontes, contratos visuais, HyperFrames, dependências e trabalhadores de voz/composição continuam idênticos. O texto do prompt do painel fica fora desse bloqueio porque não altera o MP4. Mudanças no extrator de revisão, na conferência pós-render e na entrega podem ser corrigidas sem invalidar o MP4. Uma alteração visual, editorial ou vocal pede o caminho normal de produção, que reaproveita o cache compatível.

Somente derivados são restaurados: relatórios gerados, timeline, WAVs brutos e processados, trilha contínua, música, clips, mídia preparada, capturas e os arquivos finais. O JSON editorial e qualquer fonte do checkout permanecem preservados. Links simbólicos, junções, arquivos especiais e caminhos que escapam das pastas autorizadas são recusados.

O MP4 precisa ter o mesmo SHA256 registrado no QA original, com nenhuma falha. Cada WAV bruto e processado precisa ser byte-idêntico ao manifesto aprovado; a trilha contínua também conserva seu hash. Depois da cópia, o QA mede novamente o vídeo real e continua bloqueante para integridade. A extração dos quadros e métricas visuais é diagnóstica: uma falha nessa extração fica explícita no recibo e não impede o envio do MP4 aprovado. O pacote de revisão acompanha a entrega quando foi concluído. As medidas não substituem a revisão editorial e a escuta.

Ao concluir, o workflow entrega MP4 e título/descrição na mesma nova pasta do Drive, com o pacote de revisão quando disponível. O artifact `daily-delivery-receipt` reúne a pasta final, hashes e origem da retomada; `daily-resume-receipt.json` registra os dois commits, o resultado da extração diagnóstica, a revisão semântica pendente e declara que não houve nova síntese nem render. A capa segue pelo fluxo de suplemento do chat, e a publicação no YouTube continua manual.

Artifacts expiram após sete dias. Se o artifact completo expirou, falta algum derivado necessário ou o código crítico mudou, esta recuperação não poderá certificar o reaproveitamento; a produção normal deverá retomar o cache disponível. Repetir a entrega cria uma nova pasta no Drive, portanto confira o recibo da execução anterior antes de reexecutar um envio já concluído.
