# Direção de voz editorial

A mesma voz fixa do apresentador passa a receber direção por intenção. O motor usa `prosody`, `break` e bookmarks do Azure, sem outro serviço ou nova dependência. A interpretação final depende da voz sintetizada; os parâmetros não substituem a escuta da produção.

## Contrato por cena

```json
{
  "narration": "Parece pouco. Mas esse valor muda o resultado.",
  "tts": {
    "delivery": "contrast",
    "cues": [
      {"text": "muda o resultado", "kind": "emphasis", "pause_before_ms": 100}
    ]
  }
}
```

- `hook`: abertura um pouco mais ágil, com energia moderada.
- `explain`: ritmo conversacional para acompanhar a explicação visual.
- `contrast`: respiro maior entre frases para perceber a mudança.
- `question`: pausa para absorver a pergunta; não alongar artificialmente cada palavra.
- `closing`: conclusão mais firme e ligeiramente desacelerada.

Projetos sem direção explícita recebem `hook` na primeira cena, `closing` na última e `explain` nas demais. Frases com algarismos desaceleram ligeiramente; perguntas recebem variação discreta. A alternância mecânica por índice de frase foi removida.

`cues` controla trechos curtos: `emphasis` destaca uma ideia, `number` dá clareza ao dado, `contrast` marca uma virada. `pause_before_ms` vai de 0 a 300. Cada trecho deve ser literal, único, contido numa frase e sem sobreposição. Preferir 1–3 indicações importantes por cena, no máximo seis. Não separar uma pronúncia cadastrada em partes. A produção recusa essas divisões antes de enviar a respectiva fala ao Azure.

O ritmo final fica entre -10% e +6%; a altura, entre -3% e +3%. Não há aumento de volume, troca de personagem, risadas ou efeitos de atuação automáticos. `rate`, `pitch`, `pause_ms` e `pronunciations` existentes continuam aceitos; valores extremos de ritmo/altura são limitados pelo motor.

## Sincronização e roteiro

Pausas explícitas antecedem o bookmark quando ambos começam no mesmo trecho. O render continua usando o instante real retornado pelo Azure, sem estimar duração pelo número de palavras. Ao mudar a direção de voz, gerar novamente áudio e manifesto antes do vídeo. Não reutilizar timings de uma produção anterior.

Escrever frases com uma ideia, variar comprimentos e conectar dado, exemplo e consequência. Dar espaço à compreensão dos recortes e gráficos. Não ler o texto inteiro da tela; a voz explica enquanto os elementos demonstram. O prompt diário deve elaborar a direção de fala junto com os eventos visuais.

Referência técnica: [prosody e direção de voz no Azure](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice). Não usar `express-as` sem verificar suporte da voz selecionada. Referências técnicas e fontes de pesquisa ficam nos arquivos internos, sem links na descrição do YouTube.
