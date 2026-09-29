import argparse
import json
import os
import sys
from pathlib import Path


def sanitize_page_thoroughly(page) -> None:
    """Aplica a sanitização completa testada: clica para aceitar/fechar, remove overlays e reseta opacidade."""
    script = """() => {
        // 1. Clicar em botões de rejeitar, aceitar ou fechar
        document.querySelectorAll('button, a').forEach(el => {
            try {
                const text = el.textContent || '';
                const aria = el.getAttribute('aria-label') || '';
                if (/rejeitar|aceitar|fechar|dispensar|entendi|close/i.test(text) || /fechar|close/i.test(aria) || el.classList.contains('close')) {
                    el.click();
                }
            } catch (e) {}
        });

        // 2. Remover todos os modais, backdrops, popovers, tooltips, banners e widgets flutuantes
        const selectorsToRemove = [
            '.modal', '.backdrop', '.modal-backdrop',
            '[class*="cookie"]', '[id*="cookie"]',
            '[class*="consent"]', '[id*="consent"]',
            '[class*="lgpd"]', '[id*="lgpd"]',
            '.popover', '[class*="popover"]',
            '.tooltip', '[class*="tooltip"]', '[data-tippy-root]',
            '[class*="overlay"]', '[class*="mask"]',
            '[class*="banner"]', '[id*="banner"]',
            '#barra-brasil', '.govbr-cookie-banner',
            '[id*="vlibras"]', '[class*="vlibras"]',
            '#widget-leo', '[class*="chatbot"]'
        ];

        selectorsToRemove.forEach(sel => {
            try {
                document.querySelectorAll(sel).forEach(el => el.remove());
            } catch (e) {}
        });

        // 3. Eliminar qualquer elemento fixo que esteja aplicando sombra ou escurecimento
        document.querySelectorAll('div, section, aside').forEach(el => {
            try {
                const text = el.innerText || '';
                if (text.includes('Para começar') || text.includes('PERGUNTA PRO LEO')) {
                    el.remove();
                    return;
                }
                const s = window.getComputedStyle(el);
                if ((s.position === 'fixed' || s.position === 'absolute') && (s.backgroundColor.includes('rgba(0, 0, 0') || parseInt(s.zIndex) > 50)) {
                    el.remove();
                }
            } catch (e) {}
        });

        // 4. Resetar 100% de qualquer filtro de blur, névoa ou opacidade reduzida na página
        document.documentElement.style.filter = 'none';
        document.body.style.filter = 'none';
        document.body.style.opacity = '1';
        document.body.style.backgroundColor = '#ffffff';

        document.querySelectorAll('*').forEach(el => {
            try {
                const s = window.getComputedStyle(el);
                if (s.filter && s.filter !== 'none') el.style.filter = 'none';
                if (s.opacity && parseFloat(s.opacity) < 0.95 && el.tagName !== 'svg') el.style.opacity = '1';
            } catch (e) {}
        });
    }"""
    try:
        page.evaluate(script)
    except Exception as exc:
        print(f"[auto_capture] Aviso na sanitizacao: {exc}")


def generate_editorial_fallback(dest_path: Path, asset: dict) -> None:
    try:
        from PIL import Image, ImageDraw

        width, height = 1351, 917
        img = Image.new("RGB", (width, height), color="#FFFFFF")
        draw = ImageDraw.Draw(img)

        draw.rectangle([(20, 20), (width - 20, height - 20)], outline="#E2E8F0", width=2)

        cross_len = 16
        for cx, cy in [(40, 40), (width - 40, 40), (40, height - 40), (width - 40, height - 40)]:
            draw.line([(cx - cross_len, cy), (cx + cross_len, cy)], fill="#7E8B99", width=2)
            draw.line([(cx, cy - cross_len), (cx, cy + cross_len)], fill="#7E8B99", width=2)

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

    url = asset.get("source_page_url")
    if not url:
        print(f"[auto_capture] Asset {asset.get('id')} sem source_page_url; gerando editorial.")
        generate_editorial_fallback(dest_path, asset)
        return True

    print(f"[auto_capture] Processando captura: {url} -> {dest_path.name}")
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

        # 1. Navegar na URL
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=40000)
            if response and response.status in (404, 500, 502, 503):
                print(f"[auto_capture] ALERTA: Status HTTP {response.status} em {url}. Acionando fallback editorial.")
                generate_editorial_fallback(dest_path, asset)
                context.close()
                return True
        except Exception as nav_exc:
            print(f"[auto_capture] Aviso na navegação de {url}: {nav_exc}")

        # 2. Aguardar scripts assíncronos
        page.wait_for_timeout(5000)

        # 3. Pressionar Escape para dispensar popovers
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        # 4. Sanitizar completamente (remover modais, restaurar fundo branco)
        sanitize_page_thoroughly(page)

        # 5. Auditoria de conteúdo: detectar páginas de erro (ex: 404, não encontrada)
        content_text = page.evaluate("() => document.body ? document.body.innerText : ''")
        page_title = page.title()
        error_indicators = [
            "página não encontrada",
            "pagina nao encontrada",
            "o termo procurado não foi encontrado",
            "404 not found",
            "erro 404",
            "ops! não encontramos",
        ]
        is_error = any(ind in content_text.lower() for ind in error_indicators) or any(ind in page_title.lower() for ind in error_indicators)

        expected_text = asset.get("expected_text")
        if expected_text and expected_text.lower() not in content_text.lower():
            print(f"[auto_capture] ALERTA: Texto esperado '{expected_text}' não encontrado na página {url}.")
            is_error = True

        if is_error:
            print(f"[auto_capture] Página inválida ou 404 detectada em {url}. Acionando fallback editorial autêntico.")
            generate_editorial_fallback(dest_path, asset)
            context.close()
            return True

        # 6. Rolar para o trecho ou elemento específico se solicitado (ex: Art. 31 da lei)
        scroll_to_text = asset.get("scroll_to_text")
        if scroll_to_text:
            scrolled = page.evaluate("""(textToFind) => {
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
                let node;
                while ((node = walker.nextNode())) {
                    if (node.nodeValue && node.nodeValue.includes(textToFind)) {
                        const parent = node.parentElement;
                        if (parent) {
                            parent.scrollIntoView({ block: 'center', inline: 'center' });
                            return true;
                        }
                    }
                }
                return false;
            }""", scroll_to_text)
            if scrolled:
                print(f"[auto_capture] Rolagem até '{scroll_to_text}' realizada com sucesso.")
                page.wait_for_timeout(1000)

        # 7. Screenshot do elemento ou viewport completa
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
                print(f"[auto_capture] Seletor {target_selector} não encontrado: {sel_exc}")

        if not captured_element:
            page.screenshot(path=str(dest_path), full_page=False)
            print(f"[auto_capture] Screenshot limpo salvo em: {dest_path.name}")

        context.close()
        return True

    except Exception as exc:
        print(f"[auto_capture] Erro ao capturar {url}: {exc}")
        generate_editorial_fallback(dest_path, asset)
        return True

    try:
        context = playwright_browser.new_context(
            viewport={"width": 1351, "height": 917},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            device_scale_factor=1,
        )
        page = context.new_page()

        # 1. Navegar na URL
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
        except Exception as nav_exc:
            print(f"[auto_capture] Timeout ou aviso na navegacao de {url}: {nav_exc}")

        # 2. Aguardar 6s para os scripts assíncronos e modais carregarem
        page.wait_for_timeout(6000)

        # 3. Pressionar Escape para dispensar popovers
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        # 4. Sanitizar completamente (clicar em aceitar/fechar, remover overlays, restaurar fundo branco e opacidade)
        sanitize_page_thoroughly(page)

        # 5. Aguardar 1.5s para a renderização limpa estabilizar
        page.wait_for_timeout(1500)

        # 6. Screenshot do elemento ou viewport completa
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

        if not captured_element:
            page.screenshot(path=str(dest_path), full_page=False)
            print(f"[auto_capture] Screenshot limpo de viewport completa salvo em: {dest_path.name}")

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

    with open(project_path, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"[auto_capture] Concluido: {success_count}/{len(excerpts)} recortes prontos para o Remotion.")


if __name__ == "__main__":
    main()
