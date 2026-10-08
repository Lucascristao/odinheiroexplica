import {readFileSync,existsSync} from "node:fs";
import {resolve} from "node:path";
import {createHash} from "node:crypto";
import {thumbnailContractSchema,validateThumbnailContract} from "../src/lib/thumbnail-contract";
import {stableJson} from "../src/lib/editorial-project";

const root=resolve(import.meta.dirname,"..");
const args=process.argv.slice(2);
const episodePath=resolve(root,"video/data/daily.json");
const episode=JSON.parse(readFileSync(episodePath,"utf8"));
const thumb=episode.packaging?.thumbnails?.[0];
const id=String(episode.project_id??"");
if(!/^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(id))throw Error("project_id inválido para contrato de capa.");
const legacy=resolve(root,"production",id,"thumbnail-contract.json");
const inline=thumb?.contract;
const snapshot=existsSync(legacy)?JSON.parse(readFileSync(legacy,"utf8")):null;
if(snapshot&&(snapshot.project_id!==id||snapshot.headline!==thumb?.headline))throw Error("Contrato externo corresponde a outro episódio ou headline.");
if(args.includes("--new-episode")&&!inline)throw Error("Novo episódio exige packaging.thumbnails[0].contract estruturado, antes do primeiro render.");
if(inline&&snapshot&&stableJson(inline)!==stableJson(snapshot.contract))throw Error("Contrato externo diverge do contrato canônico do episódio.");
const candidate=inline??snapshot?.contract;
if(!candidate)throw Error("Falta contrato de capa. Preencha packaging.thumbnails[0].contract; legado exige production/EPISODIO/thumbnail-contract.json.");
const errors=validateThumbnailContract(episode,candidate);
if(errors.length)throw Error(errors.join("\n"));
const c=thumbnailContractSchema.parse(candidate);
const contractSha=createHash("sha256").update(stableJson(c)).digest("hex");
const sourceSha=createHash("sha256").update(readFileSync(episodePath).toString("utf8").replaceAll("\r\n","\n")).digest("hex");
if(args.includes("--check")) {
  console.log(`Thumbnail OK: ${id}; headline ${JSON.stringify(c.exact_headline)}; SHA ${contractSha.slice(0,12)}; origem ${inline?"daily.json":"snapshot legado"}.`);
} else {
  const prompt=[
    "GERAR CAPA FINAL 1280 x 720, 16:9. Usar somente o episódio e o contrato abaixo, sem acrescentar personagens nem objetos por iniciativa própria.",
    `HEADLINE EXATA, ÚNICO TEXTO VISÍVEL: ${JSON.stringify(c.exact_headline)}`,
    `PROTAGONISTA: ${c.primary_subject}`,
    `APOIO SECUNDÁRIO: ${c.secondary_subject??"nenhum"}`,
    `TENSÃO VISUAL: ${c.visual_tension}`,
    `COMPOSIÇÃO: ${c.composition}`,
    `CORES: fundo/base ${c.palette.base}, amarelo ${c.palette.accent}, branco ${c.palette.text}; cinematográfico, editorial, legível em 320x180.`,
    `PROIBIDO INCLUIR (todos os itens): ${c.forbidden_elements.join("; ")}.`,
    "Nenhum outro texto, número, rosto, documento ou ícone além dos explicitamente autorizados. Não reproduzir uma fórmula visual de outro episódio.",
    "Depois da geração, INSPECIONAR a imagem real e criar thumbnail-audit.json vinculado aos hashes; não atestar o que não foi observado.",
  ].join("\n");
  console.log(JSON.stringify({project_id:id,title:episode.title,contract_sha256:contractSha,source_project_sha256:sourceSha,contract:c,prompt,scope:"Contrato estrutural; não verifica semanticamente pixels nem substitui revisão perceptual."},null,2));
}
