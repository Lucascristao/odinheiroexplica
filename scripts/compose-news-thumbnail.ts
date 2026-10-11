import {readFileSync,writeFileSync,mkdirSync,existsSync,realpathSync} from "node:fs";
import {resolve,relative,isAbsolute,extname} from "node:path";
import {createHash} from "node:crypto";
import {bundle} from "@remotion/bundler";
import {selectComposition,renderStill} from "@remotion/renderer";
import {thumbnailContractSchema} from "../src/lib/thumbnail-contract";
import {stableJson} from "../src/lib/editorial-project";

const root=resolve(import.meta.dirname,"..");
const args=process.argv.slice(2);
const option=(key:string)=>{const i=args.indexOf(key);return i<0?undefined:args[i+1];};
const projectFile=option("--project"),backgroundFile=option("--background");
if(!projectFile||!backgroundFile)throw Error("Exige --project PROJETO --background FUNDO aprovado sem texto/rostos; não gera outro apresentador.");
const project=JSON.parse(readFileSync(resolve(root,projectFile),"utf8"));
if(!/^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(project.project_id))throw Error("project_id inválido.");
const contract=thumbnailContractSchema.parse(project.packaging?.thumbnails?.[0]?.contract);
const identity=contract.presenter_identity;
if(!identity)throw Error("O contrato deste episódio não autoriza o retrato do Roberto.");
const policy=JSON.parse(readFileSync(resolve(root,"worker/presenter-identity.json"),"utf8"));
const registered=policy.identities[identity.id];
if(!registered||registered.mode!==identity.mode||registered.reference_path!==identity.reference_path||registered.reference_sha256!==identity.reference_sha256)throw Error("Referência diferente da identidade oficial.");
const hash=(data:Buffer|string)=>createHash("sha256").update(data).digest("hex");
const portraitPath=realpathSync(resolve(root,identity.reference_path));
const inside=(path:string)=>{const rel=relative(realpathSync(root),path);return !isAbsolute(rel)&&rel!==".."&&!rel.startsWith("../")&&!rel.startsWith("..\\");};
if(!inside(portraitPath))throw Error("Retrato fora do repositório.");
const portrait=readFileSync(portraitPath);
if(hash(portrait)!==identity.reference_sha256)throw Error("Retrato oficial foi alterado; não recriar o rosto.");
const backgroundPath=realpathSync(resolve(root,backgroundFile));
if(!inside(backgroundPath)||![".png",".jpg",".jpeg"].includes(extname(backgroundPath).toLowerCase()))throw Error("Fundo deve ser imagem dentro do repositório.");
const background=readFileSync(backgroundPath);
const portraitSide=option("--portrait-side")??"right";
if(!["left","right"].includes(portraitSide))throw Error("--portrait-side aceita left ou right.");
const headlinePosition=option("--headline-position")??"lower",portraitSize=option("--portrait-size")??"close";
if(!["upper","middle","lower"].includes(headlinePosition))throw Error("--headline-position aceita upper, middle ou lower.");
if(!["compact","standard","close"].includes(portraitSize))throw Error("--portrait-size aceita compact, standard ou close.");
const directory=resolve(root,"production",project.project_id);
mkdirSync(directory,{recursive:true});
const output=resolve(directory,"thumbnail.jpg"),receiptPath=resolve(directory,"thumbnail-composition.json");
const contractHash=hash(stableJson(contract));
if(existsSync(output)&&!args.includes("--replace"))throw Error("Capa já existe. Revise o episódio antes de usar --replace.");
const dataUrl=(bytes:Buffer,mime:string)=>`data:${mime};base64,${bytes.toString("base64")}`;
const inputProps={headline:contract.exact_headline,portrait:dataUrl(portrait,"image/png"),
  background:dataUrl(background,extname(backgroundPath).toLowerCase()===".png"?"image/png":"image/jpeg"),
  portraitSide:portraitSide as "left"|"right",headlinePosition:headlinePosition as "upper"|"middle"|"lower",
  portraitSize:portraitSize as "compact"|"standard"|"close"};
const serveUrl=await bundle({entryPoint:resolve(root,"video/src/LockedPresenterThumbnail.tsx"),publicDir:resolve(root,"video/public")});
const composition=await selectComposition({serveUrl,id:"LockedPresenterThumbnail",inputProps});
await renderStill({composition,serveUrl,inputProps,output,imageFormat:"jpeg",jpegQuality:92,overwrite:true});
const image=readFileSync(output);
if(image.length>2_000_000)throw Error("Capa excedeu 2 MB; não enviar.");
writeFileSync(receiptPath,JSON.stringify({version:"locked-presenter-cover-v1",project_id:project.project_id,
  contract_sha256:contractHash,identity_id:identity.id,portrait_sha256:identity.reference_sha256,
  image_sha256:hash(image),background_path:relative(root,backgroundPath).replaceAll("\\","/"),
  background_sha256:hash(background),portrait_side:portraitSide,headline_position:headlinePosition,
  portrait_size:portraitSize,created_at:new Date().toISOString()},null,2)+"\n");
console.log(JSON.stringify({image:relative(root,output),receipt:relative(root,receiptPath),identity:identity.id,
  next:"Inspecionar a capa final e a leitura em 320x180; somente então gravar thumbnail-audit.json. O recibo não substitui inspeção."},null,2));
