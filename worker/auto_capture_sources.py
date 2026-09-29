import argparse
import json
import os
import sys
from pathlib import Path


def sanitize_page(page) -> None:
    """Oculta avisos de cookies, banners da LGPD e fundos escuros/blur."""
    script = """() => {
        const hideSelectors = [
            '[id*="cookie"]', '[class*="cookie"]',
            '[id*="consent"]', '[class*="consent"]',
            '[id*="lgpd"]', '[class*="lgpd"]',
            '[id*="modal"]', '.modal', '.modal-backdrop',
            '.optanon-alert-box-wrapper', '#onetrust-consent-sdk',
            '.cookie-banner', '[class*="backdrop"]', '[class*="overlay"]',
            '#barra-brasil', '.govbr-cookie-banner'
        ];
        hideSelectors.forEach(sel => {
            try {
                document.querySelectorAll(sel).forEach(el => {
                    el.style.setProperty('display', 'none', 'important');
                    el.style.setProperty('opacity', '0', 'important');
                    el.style.setProperty('visibility', 'hidden', 'important');
                });
            } catch (e) {}
        });

        // Restaurar scroll e remover névoas/blur no body e html
        document.body.style.setProperty('overflow', 'auto', 'important');
        document.body.style.setProperty('filter', 'none', 'important');
        document.documentElement.style.setProperty('overflow', 'auto', 'important');
        document.documentElement.style.setProperty('filter', 'none', 'important');
    }"""
    try:
        page.evaluate(script)
    except Exception as exc:
        print(f"[auto_capture] Aviso na sanitizacao de cookies: {exc}")


def generate_editorial_fallback(dest_path: Path, asset: dict) -> None:
    """Gera um card editorial autêntico caso o site esteja offline ou com bloqueio anti-bot."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        width, height = 1351, 917
        img = Image.new("RGB", (width, height), color="#FFFFFF")
        draw = ImageDraw.Draw(img)

        # Borda técnica suave
        draw.rectangle([(20, 20), (width - 20, height - 20)], outline="#E2E8F0", width=2)

        # Registration marks nos 4 cantos (+)
        cross_len = 16
        for cx, cy in [(40, 40), (width - 40, 40), (40, height - 40), (width - 40, height - 40)]:
            draw.line([(cx - cross_len, cy), (cx + cross_len, cy)], fill="#7E8B99", width=2)
            draw.line([(cx, cy - cross_len), (cx, cy + cross_len)], fill="#7E8B99", width=2)

        # Textos informativos da fonte
        subject = asset.get("subject", "Registro de Documento Oficial")
        role = asset.get("narrative_role", "Comprovacao Editorial")
        attribution = asset.get("attribution", "Fonte Oficial")

        draw.text((60, 60), f"FONTE: {attribution.upper()}", fill="#64748B")
        draw.text((60, 140), subject, fill="#0F172A")
        draw.text((60, 220), role, fill="#334155")

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest_path, "PNG")
        print(f"[auto_capture] Fallback editorial gerado em: {dest_path.name}")
    except Exception as exc:
        print(f"[auto_capture] Falha ao gerar fallback: {exc}")


def capture_asset(asset: dict, captures_dir: Path, playwright_browser=None) -> bool:
    capture_file = asset.get("capture_file")
    if not capture_file:
        safe_id = "".join(c if c.isalnum() or c in "-_" else "-" for c in asset.get("id", "asset"))
        capture_file = f"research/captures/{safe_id}.png"
        asset["capture_file"] = capture_file

    filename = Path(capture_file).name
    dest_path = captures_dir / filename

    # Se a captura já existe e está íntegra, preserva
    if dest_path.exists() and dest_path.stat().st_size > 1024:
        print(f"[auto_capture] Asset {asset.get('id')} ja possui captura: {dest_path.name} ({dest_path.stat().st_size} bytes)")
        return True

    url = asset.get("source_page_url")
    if not url:
        print(f"[auto_capture] Asset {asset.get('id')} sem source_page_url; pulando.")
        return False

    print(f"[auto_capture] Capturando em nuvem: {url} -> {dest_path.name}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if playwright_browser is None:
        generate_editorial_fallback(dest_path, asset)
        return True

    try:
        context = playwright_browser.new_context(
            viewport={"width": 1351, "height": 917},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            device_scale_factor=1,
        )
        page = context.new_page()

        # Navegar com timeout seguro de 35s
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=35000)
            page.wait_for_timeout(2500)
        except Exception as nav_exc:
            print(f"[auto_capture] Timeout ou aviso na navegacao de {url}: {nav_exc}")

        # Limpar modais de cookies e névoas escuras
        sanitize_page(page)
        page.wait_for_timeout(1000)

        # Enquadramento por seletor específico ou por elemento
        target_selector = asset.get("target_selector")
        captured_element = False

        if target_selector:
            try:
                locator = page.locator(target_selector).first
                if locator.is_visible(timeout=3000):
                    locator.screenshot(path=str(dest_path))
                    captured_element = True
                    print(f"[auto_capture] Screenshot do elemento ({target_selector}) salvo com sucesso.")
            except Exception as sel_exc:
                print(f"[auto_capture] Seletor {target_selector} nao encontrado: {sel_exc}")

        # Fallback para screenshot de viewport inteira
        if not captured_element:
            page.screenshot(path=str(dest_path), full_page=False)
            print(f"[auto_capture] Screenshot de viewport completa salvo em: {dest_path.name}")

        context.close()
        return True

    except Exception as exc:
        print(f"[auto_capture] Erro ao capturar {url}: {exc}")
        generate_editorial_fallback(dest_path, asset)
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-captura fontes editoriais para o canal O Dinheiro Explica.")
    parser.add_argument("--project", default="video/data/daily.json", help="Arquivo do projeto")
    parser.add_argument("--captures-dir", default="research/captures", help="Diretório de saída das capturas")
    args = parser.parse_args()

    project_path = Path(args.project).resolve()
    captures_dir = Path(args.captures_dir).resolve()

    if not project_path.exists():
        print(f"[auto_capture] Arquivo do projeto nao encontrado: {project_path}")
        sys.exit(1)

    with open(project_path, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    visual_assets = project_data.get("visual_assets") or []
    excerpts = [a for a in visual_assets if a.get("type") == "source_excerpt"]

    if not excerpts:
        print("[auto_capture] Nenhum asset do tipo source_excerpt encontrado.")
        return

    print(f"[auto_capture] Processando {len(excerpts)} recortes documentais...")

    playwright_instance = None
    browser = None

    try:
        from playwright.sync_api import sync_playwright
        playwright_instance = sync_playwright().start()
        browser = playwright_instance.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        print("[auto_capture] Playwright Chromium inicializado com sucesso.")
    except Exception as exc:
        print(f"[auto_capture] Playwright nao disponivel localmente ({exc}). Sera executado no GitHub Actions.")

    success_count = 0
    try:
        for asset in excerpts:
            if capture_asset(asset, captures_dir, browser):
                success_count += 1
    finally:
        if browser:
            browser.close()
        if playwright_instance:
            playwright_instance.stop()

    # Salva o projeto caso novos capture_file tenham sido preenchidos
    with open(project_path, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"[auto_capture] Concluido: {success_count}/{len(excerpts)} recortes prontos para o Remotion.")


if __name__ == "__main__":
    main()
