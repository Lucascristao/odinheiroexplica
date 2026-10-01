"""Canonical scene access for both portable project formats."""
import copy
import json


def normalize_project(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("Projeto editorial deve ser um objeto.")
    root = raw.get("scenes")
    nested = (raw.get("script") or {}).get("scenes")
    if root is not None and nested is not None and root != nested:
        raise ValueError("scenes e script.scenes divergem; escolha uma única versão.")
    scenes = root if root is not None else nested
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Projeto sem cenas.")
    result = copy.deepcopy(raw)
    normalized = []
    for i, scene in enumerate(scenes):
        item = copy.deepcopy(scene)
        index = item.get("scene_index", item.get("index", i))
        item.update(id=item.get("id") or f"scene-{int(index):02d}", scene_index=index, index=index)
        normalized.append(item)
    if len({s['id'] for s in normalized}) != len(normalized):
        raise ValueError("ID de cena duplicado.")
    result["scenes"] = normalized
    result["script"] = {**(result.get("script") or {}), "scenes": normalized}
    return result


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    project = normalize_project(json.loads(Path(args.input).read_text(encoding="utf-8")))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(project, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Projeto canônico: {len(project['scenes'])} cenas em {out}")
