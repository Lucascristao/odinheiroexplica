"""Deliver the chat-created final cover/review to the verified episode folder."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from drive import uploader_from_env
from upload_outputs_to_drive import safe_name
from thumbnail_contract import validate_thumbnail_audit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder-id",required=True)
    parser.add_argument("--asset",required=True)
    parser.add_argument("--role",choices=["thumbnail","editorial-review"],required=True)
    parser.add_argument("--output",default="render-output/daily-supplement-drive.json")
    args=parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,}",args.folder_id):
        raise ValueError("ID de pasta inválido.")
    root=Path(__file__).resolve().parents[1]
    path=(root/args.asset).resolve()
    if not path.is_relative_to(root/"production") or not path.is_file():
        raise ValueError("Suplemento deve existir em production/ no Git.")
    if args.role=="thumbnail":
        from PIL import Image
        with Image.open(path) as image:
            if path.suffix.lower() not in [".jpg",".jpeg",".png"] or image.width<1280 or abs(image.width/image.height-16/9)>.01 or path.stat().st_size>2*1024*1024:
                raise ValueError("Capa final exige 16:9, pelo menos 1280px e no máximo 2MiB.")
    elif path.suffix.lower() not in [".md",".json"]:
        raise ValueError("Revisão deve ser Markdown ou JSON.")
    # Block submission before opening the Drive client if editorial visual evidence is missing.
    project=json.loads((root/"video/data/daily.json").read_text(encoding="utf-8"))
    thumbnail_audit=validate_thumbnail_audit(root,project,path) if args.role=="thumbnail" else None
    uploader=uploader_from_env()
    if uploader is None:
        raise RuntimeError("Drive não configurado.")
    folder=uploader.service.files().get(fileId=args.folder_id,fields="id,name,parents,mimeType,webViewLink").execute()
    if folder["mimeType"]!="application/vnd.google-apps.folder" or uploader.folder_id not in folder.get("parents",[]) or not folder["name"].startswith(safe_name(project["project_id"])+"_"):
        raise ValueError("A pasta não corresponde à produção atual dentro do destino configurado.")
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    name=f"{args.role}-{digest[:12]}{path.suffix.lower()}"
    existing=uploader.service.files().list(q=f"'{args.folder_id}' in parents and name = '{name}' and trashed = false",fields="files(id,name)").execute().get("files",[])
    file_id=existing[0]["id"] if existing else uploader.upload(path,name,folder_id=args.folder_id)
    verified=uploader.service.files().get(fileId=file_id,fields="id,name,parents,size,md5Checksum,webViewLink").execute()
    if args.folder_id not in verified.get("parents",[]) or int(verified.get("size",-1))!=path.stat().st_size or verified.get("md5Checksum")!=hashlib.md5(path.read_bytes()).hexdigest():
        raise RuntimeError("Readback do Drive diverge do arquivo enviado.")
    audit_verified=None
    if thumbnail_audit:
        audit_path=thumbnail_audit["audit_path"]
        audit_name=f"thumbnail-audit-{thumbnail_audit['audit_sha256'][:12]}.json"
        found=uploader.service.files().list(q=f"'{args.folder_id}' in parents and name = '{audit_name}' and trashed = false",fields="files(id,name)").execute().get("files",[])
        audit_id=found[0]["id"] if found else uploader.upload(audit_path,audit_name,folder_id=args.folder_id)
        audit_verified=uploader.service.files().get(fileId=audit_id,fields="id,name,parents,size,md5Checksum,webViewLink").execute()
        if args.folder_id not in audit_verified.get("parents",[]) or int(audit_verified.get("size",-1))!=audit_path.stat().st_size or audit_verified.get("md5Checksum")!=hashlib.md5(audit_path.read_bytes()).hexdigest():
            raise RuntimeError("Readback da auditoria da thumbnail falhou.")
    folder_files=[]
    page_token=None
    while True:
        page=uploader.service.files().list(q=f"'{args.folder_id}' in parents and trashed = false",fields="nextPageToken,files(id,name,mimeType,size,md5Checksum,webViewLink)",pageSize=100,pageToken=page_token).execute()
        folder_files.extend(page.get("files",[]))
        page_token=page.get("nextPageToken")
        if not page_token:
            break
    source_hash=hashlib.sha256((root/"video/data/daily.json").read_bytes().replace(b"\r\n",b"\n")).hexdigest()
    result={"project_id":project["project_id"],"source_project_sha256":source_hash,"folder":folder,"folder_files":folder_files,"role":args.role,"file":verified,"source_path":args.asset,"sha256":digest,"verified_readback":True,"thumbnail_audit":audit_verified,"thumbnail_contract_sha256":thumbnail_audit["contract_sha256"] if thumbnail_audit else None}
    output=root/args.output
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))


if __name__=="__main__":
    main()
