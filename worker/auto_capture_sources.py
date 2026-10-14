import argparse
import json
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, urlparse


NAVIGATION_RETRY_ATTEMPTS = 3
_EVALUATE_WITHOUT_ARG = object()


def is_transient_navigation_error(exc: Exception) -> bool:
    message = str(exc).casefold()
    return any(
        marker in message
        for marker in (
            "execution context was destroyed",
            "most likely because of a navigation",
            "cannot find context with specified id",
            "frame was detached",
            "page is navigating",
        )
    )


def wait_for_page_settle(page) -> None:
    """Espera a navegação terminar sem transformar network-idle em requisito."""
    for state in ("domcontentloaded", "load"):
        try:
            page.wait_for_load_state(state, timeout=10000)
        except Exception:
            pass
    try:
        page.wait_for_timeout(750)
    except Exception:
        pass


def evaluate_with_navigation_retry(
    page,
    script: str,
    arg=_EVALUATE_WITHOUT_ARG,
    *,
    operation_name: str = "avaliar a página",
):
    last_error = None
    for attempt in range(1, NAVIGATION_RETRY_ATTEMPTS + 1):
        try:
            if arg is _EVALUATE_WITHOUT_ARG:
                return page.evaluate(script)
            return page.evaluate(script, arg)
        except Exception as exc:
            last_error = exc
            if (
                not is_transient_navigation_error(exc)
                or attempt == NAVIGATION_RETRY_ATTEMPTS
            ):
                raise
            print(
                f"[auto_capture] Navegação transitória ao {operation_name}; "
                f"aguardando e tentando novamente ({attempt}/"
                f"{NAVIGATION_RETRY_ATTEMPTS})."
            )
            wait_for_page_settle(page)
    raise last_error  # pragma: no cover


def title_with_navigation_retry(page) -> str:
    last_error = None
    for attempt in range(1, NAVIGATION_RETRY_ATTEMPTS + 1):
        try:
            return page.title()
        except Exception as exc:
            last_error = exc
            if (
                not is_transient_navigation_error(exc)
                or attempt == NAVIGATION_RETRY_ATTEMPTS
            ):
                raise
            print(
                "[auto_capture] Navegação transitória ao ler o título; "
                f"aguardando e tentando novamente ({attempt}/"
                f"{NAVIGATION_RETRY_ATTEMPTS})."
            )
            wait_for_page_settle(page)
    raise last_error  # pragma: no cover


def sanitize_page_thoroughly(page) -> None:
    """Aplica a sanitização completa testada: clica para aceitar/fechar, remove overlays e reseta opacidade."""
    script = """() => {
        // 1. Nunca clicar em links nem em botões de consentimento ao capturar
        // fonte jornalística: links "aceitar/fechar" podem disparar redirecionamento
        // ou recriar o body enquanto estamos fazendo o screenshot. Somente
        // neutralizar overlays sem alterar o texto do próprio documento.
        if (!document.body) return;

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
            // The government navigation web component contains a Shadow DOM
            // scrim. Outer-page visibility/filter resets do not reach it.
            '#barra-brasil', '#barra-govbr', 'barra-govbr', '.govbr-cookie-banner',
            '[id*="vlibras"]', '[class*="vlibras"]',
            '#widget-leo', '[class*="chatbot"]'
        ];

        selectorsToRemove.forEach(sel => {
            try {
                document.querySelectorAll(sel).forEach(el => {
                    if (el.querySelector('.conteudo-noticia, article, main, h1, .materia-conteudo') || el.closest('.conteudo-noticia, article, main')) return;
                    el.remove();
                });
            } catch (e) {}
        });

        // 3. Eliminar qualquer elemento fixo que esteja aplicando sombra ou escurecimento
        document.querySelectorAll('div, section, aside').forEach(el => {
            try {
                if (el.querySelector('.conteudo-noticia, article, main, h1, .materia-conteudo') || el.closest('.conteudo-noticia, article, main')) return;
                const text = el.innerText || el.textContent || '';
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
        if (!document.body || !document.documentElement) return;
        document.documentElement.style.filter = 'none';
        document.body.style.filter = 'none';
        document.body.style.opacity = '1';
        document.body.style.backgroundColor = '#ffffff';

        document.querySelectorAll('*').forEach(el => {
            try {
                const s = window.getComputedStyle(el);
                // Floating navigation can cover the verified heading even
                // when its bounding box is fully captured. Keep its content
                // in document flow so it cannot obscure the excerpt.
                if (s.position === 'sticky' || s.position === 'fixed') {
                    el.style.position = 'static';
                }
                if (s.filter && s.filter !== 'none') el.style.filter = 'none';
                if (s.opacity && parseFloat(s.opacity) < 0.95 && el.tagName !== 'svg') el.style.opacity = '1';
            } catch (e) {}
        });
    }"""
    try:
        evaluate_with_navigation_retry(
            page,
            script,
            operation_name="sanitizar a página",
        )
    except Exception as exc:
        print(f"[auto_capture] Aviso na sanitizacao: {exc}")


def validate_source_asset(asset: dict) -> tuple[str, str]:
    """Exige um documento identificável e uma frase verificável antes de abrir o navegador."""
    asset_id = asset.get("id", "<sem id>")
    url = asset.get("source_page_url")
    expected_text = asset.get("expected_text")
    if not isinstance(url, str) or not url.strip():
        raise RuntimeError(f"Asset {asset_id}: source_excerpt exige source_page_url específica.")
    url = url.strip()
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]
    meaningful_query = any(
        not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid"}
        for key in parse_qs(parsed.query)
    )
    has_document_path = len(path_parts) >= 2 or (
        len(path_parts) == 1
        and ("." in path_parts[0] or ("-" in path_parts[0] and len(path_parts[0]) >= 16))
    )
    if parsed.scheme != "https" or not parsed.netloc or not (has_document_path or meaningful_query):
        raise RuntimeError(
            f"Asset {asset_id}: source_page_url deve ser HTTPS e apontar para uma página específica, não uma homepage ou seção: {url}"
        )
    if not isinstance(expected_text, str) or len(expected_text.strip()) < 8:
        raise RuntimeError(
            f"Asset {asset_id}: source_excerpt exige expected_text com uma frase do documento (mínimo 8 caracteres)."
        )
    return url, expected_text.strip()


def unobscure_excerpt(locator) -> None:
    """Hide floating UI outside the proof block, retaining its original text."""
    locator.scroll_into_view_if_needed()
    locator.evaluate(r"""async target => {
        const originalText = target.textContent;
        const paint = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        const style = document.createElement('style');
        style.textContent = '[data-ode-hidden-ui], [data-ode-hidden-ui] * { visibility: hidden !important; animation: none !important; transition: none !important; }';
        document.head.appendChild(style);
        const overlaps = (el, box) => {
            if (target.contains(el) || el.contains(target)) return false;
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0 && r.right > box.left && r.left < box.right && r.bottom > box.top && r.top < box.bottom;
        };
        // visibility is inherited, but a descendant may explicitly set it back
        // to visible. Hide each outside subtree completely and allow its paint
        // to settle before Chromium captures the proof. Repeat after responsive
        // UI updates caused by scrolling, without rewriting source content.
        let clearPaints = 0;
        for (let pass = 0; pass < 8; pass++) {
            const box = target.getBoundingClientRect();
            for (const el of document.querySelectorAll('*')) {
                if (!overlaps(el, box)) continue;
                el.setAttribute('data-ode-hidden-ui', 'true');
                el.style.setProperty('transition', 'none', 'important');
                el.style.setProperty('animation', 'none', 'important');
                el.style.setProperty('visibility', 'hidden', 'important');
                for (const child of el.querySelectorAll('*')) {
                    child.style.setProperty('transition', 'none', 'important');
                    child.style.setProperty('animation', 'none', 'important');
                    child.style.setProperty('visibility', 'hidden', 'important');
                }
            }
            await paint();
            await new Promise(resolve => setTimeout(resolve, 100));
            // Responsive widgets may mount or move after source-font layout.
            // Re-measure before accepting the proof, instead of failing on UI
            // that appeared only during the previous paint.
            const settledBox = target.getBoundingClientRect();
            const clear = ![...document.querySelectorAll('*')].some(el => overlaps(el, settledBox) && getComputedStyle(el).visibility === 'visible');
            clearPaints = clear ? clearPaints + 1 : 0;
            if (clearPaints >= 2) break;
        }
        const box = target.getBoundingClientRect();
        const remaining = [...document.querySelectorAll('*')].filter(el => overlaps(el, box) && getComputedStyle(el).visibility === 'visible');
        if (remaining.length) throw new Error('UI ainda cobre o bloco de evidência: ' + remaining.slice(0, 3).map(el => el.tagName + '.' + el.className).join(', '));
        if (target.textContent !== originalText) throw new Error('O texto da fonte mudou durante a captura; revise o documento.');
    }""")


def desktop_context_clip(box, scroll_y, viewport_width, viewport_height, document_height):
    """Keep real desktop surroundings and the complete verified proof block."""
    if not box or box["height"] <= 0 or box["width"] <= 0:
        raise RuntimeError("Trecho sem região visível; não criar captura isolada.")
    if box['x'] < 0 or box['x'] + box['width'] > viewport_width + 1:
        raise RuntimeError('Trecho sai da largura desktop; não cortar informação para capturar.')
    height = min(document_height, max(viewport_height, box["height"] + 360))
    top = max(0, min(document_height - height, scroll_y + box["y"] - 240))
    return {"x": 0, "y": top, "width": viewport_width, "height": height}


def capture_desktop_context(page, expected_text, target_selector, temp_path):
    """Screenshot the actual page, never a paragraph-only element screenshot."""
    if target_selector:
        locator = page.locator(target_selector).first
        if not locator.is_visible(timeout=3000):
            raise RuntimeError("target_selector não visível para captura contextual.")
    else:
        selected = evaluate_with_navigation_retry(page, r"""(expected) => {
            const normalize = value => (value || '').replace(/\s+/g, ' ').trim().toLocaleLowerCase();
            const needle = normalize(expected);
            const candidates = [...document.querySelectorAll('p,li,tr,td,h1,h2,h3,blockquote,div,section,span,article,main')]
                .filter(el => el.getClientRects().length && normalize(el.innerText || el.textContent).includes(needle));
            candidates.sort((a,b) => normalize(a.innerText || a.textContent).length - normalize(b.innerText || b.textContent).length);
            if (!candidates.length) return false;
            candidates[0].setAttribute('data-ode-context-proof', 'true');
            return true;
        }""", expected_text, operation_name="localizar a prova na página desktop")
        if not selected:
            raise RuntimeError("Trecho contextual não localizado.")
        locator = page.locator('[data-ode-context-proof="true"]').first
    locator_text = locator.inner_text() or locator.text_content() or ""
    if " ".join(expected_text.casefold().split()) not in " ".join(locator_text.casefold().split()):
        raise RuntimeError("O bloco contextual não contém o trecho literal verificado.")
    # Keep a separate authentic introduction to the article. Never merge,
    # relocate or regenerate its masthead, headline or original byline.
    header = page.locator('h1').first
    context_expected = None
    context_path = temp_path.with_name(temp_path.stem + '.context.png')
    if header.count() and header.is_visible():
        context_expected = header.inner_text().strip()
        unobscure_excerpt(header)
        geometry = evaluate_with_navigation_retry(page, "() => ({scrollY:window.scrollY,width:window.innerWidth,height:window.innerHeight,documentHeight:document.documentElement.scrollHeight})")
        context_clip = desktop_context_clip(header.bounding_box(), geometry["scrollY"], geometry["width"], geometry["height"], geometry["documentHeight"])
        # Retain the authentic masthead/article column while excluding unrelated
        # sidebar players. The verified headline remains complete.
        header_box = header.bounding_box()
        context_clip['width'] = min(context_clip['width'], max(960, header_box['x'] + header_box['width'] + 48))
        page.screenshot(path=str(context_path), full_page=True, clip=context_clip, animations="disabled")
    else:
        page.evaluate('() => window.scrollTo(0,0)')
        page.screenshot(path=str(context_path), animations="disabled")
    unobscure_excerpt(locator)
    geometry = evaluate_with_navigation_retry(page, "() => ({scrollY:window.scrollY,width:window.innerWidth,height:window.innerHeight,documentHeight:document.documentElement.scrollHeight})")
    box = locator.bounding_box()
    clip = desktop_context_clip(box, geometry["scrollY"], geometry["width"], geometry["height"], geometry["documentHeight"])
    page.screenshot(path=str(temp_path), full_page=True, clip=clip, animations="disabled")
    return {"capture_scope": "desktop_context", "clip": clip, "context_expected_text": context_expected,
            "context_image_sha256": hashlib.sha256(context_path.read_bytes()).hexdigest(),
            "proof_region": {"x": box['x']/clip['width']*100,
                             "y": (geometry['scrollY']+box['y']-clip['y'])/clip['height']*100,
                             "width": box['width']/clip['width']*100,"height": box['height']/clip['height']*100},
            "viewport": {"width": geometry["width"], "height": geometry["height"]}}


def capture_asset(asset: dict, captures_dir: Path, playwright_browser=None) -> bool:
    url, expected_text = validate_source_asset(asset)
    capture_file = asset.get("capture_file")
    if not capture_file:
        safe_id = "".join(c if c.isalnum() or c in "-_" else "-" for c in asset.get("id", "asset"))
        capture_file = f"research/captures/{safe_id}.png"
        asset["capture_file"] = capture_file

    declared = PurePosixPath(str(capture_file))
    if "\\" in str(capture_file) or ".." in declared.parts or declared.parts[:2] != ("research", "captures") or len(declared.parts) < 3:
        raise RuntimeError(f"Asset {asset.get('id')}: capture_file deve permanecer em research/captures/.")
    relative = declared.relative_to("research/captures")
    dest_path = (captures_dir / Path(*relative.parts)).resolve()
    if not dest_path.is_relative_to(captures_dir.resolve()):
        raise RuntimeError(f"Asset {asset.get('id')}: destino fora da pasta de capturas.")
    pinned_hash = asset.get("capture_sha256")
    if pinned_hash is not None:
        receipt_path = dest_path.with_suffix(".provenance.json")
        if (not isinstance(pinned_hash, str) or len(pinned_hash) != 64 or not dest_path.is_file()
            or hashlib.sha256(dest_path.read_bytes()).hexdigest() != pinned_hash or not receipt_path.is_file()):
            raise RuntimeError("Captura revisada ausente/alterada; não reutilizar coordenadas de outra imagem.")
        proof = json.loads(receipt_path.read_text(encoding="utf-8"))
        if (proof.get("mode") not in ("authentic_page_capture", "authentic_pdf_page")
            or proof.get("source_page_url") != url or proof.get("expected_text") != expected_text
            or proof.get("image_sha256") != pinned_hash or not proof.get("captured_at")):
            raise RuntimeError("Proveniência da captura revisada não corresponde ao documento.")
        if asset.get("capture_scope") == "desktop_context" and proof.get("mode") != "authentic_pdf_page":
            from PIL import Image
            with Image.open(dest_path) as original:
                width, height = original.size
            if proof.get("capture_scope") != "desktop_context" or width < 1200 or height < 720:
                raise RuntimeError("Captura fixada mostra só um bloco: exigir página desktop com contexto antes dos zooms.")
            context_file = dest_path.with_name(dest_path.stem + '.context.png')
            if not context_file.is_file() or hashlib.sha256(context_file.read_bytes()).hexdigest() != proof.get('context_image_sha256'):
                raise RuntimeError("Captura contextual da manchete ausente ou alterada.")
        print(f"[auto_capture] Captura autêntica revisada preservada: {dest_path.name}")
        return True
    if playwright_browser is None:
        raise RuntimeError(f"Asset {asset.get('id')}: navegador Playwright indisponível; nenhuma captura foi criada.")

    print(f"[auto_capture] Processando captura: {url} -> {dest_path.name}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_name(f".{dest_path.stem}.tmp.png")
    context = None
    try:
        context = playwright_browser.new_context(
            viewport={"width": 1360, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            device_scale_factor=2,
        )
        page = context.new_page()

        response = page.goto(url, wait_until="domcontentloaded", timeout=40000)
        if response is None or response.status >= 400:
            status = response.status if response else "sem resposta HTTP"
            raise RuntimeError(f"página retornou {status}")

        # 2. Aguardar scripts assíncronos e qualquer redirecionamento tardio
        page.wait_for_timeout(5000)
        wait_for_page_settle(page)

        # 3. Pressionar Escape para dispensar popovers
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        # 4. Sanitizar completamente (remover modais, restaurar fundo branco).
        # Alguns portais recarregam a página ao aceitar/rejeitar cookies, então
        # esperamos novamente antes de ler o DOM.
        sanitize_page_thoroughly(page)
        wait_for_page_settle(page)

        # 5. Auditoria de conteúdo: detectar páginas de erro (ex: 404, não encontrada)
        content_text = evaluate_with_navigation_retry(
            page,
            "() => document.body ? (document.body.innerText?.trim() ? document.body.innerText : (document.body.textContent || '')) : ''",
            operation_name="ler o conteúdo",
        )
        if len(content_text.strip()) < 50:
            try:
                page.wait_for_selector(".conteudo-noticia, article, main, p", timeout=8000)
                content_text = evaluate_with_navigation_retry(
                    page,
                    "() => document.body ? (document.body.innerText?.trim() ? document.body.innerText : (document.body.textContent || '')) : ''",
                    operation_name="reler o conteúdo após espera",
                )
            except Exception:
                pass
        page_title = title_with_navigation_retry(page)
        error_indicators = [
            "página não encontrada",
            "pagina nao encontrada",
            "o termo procurado não foi encontrado",
            "404 not found",
            "erro 404",
            "ops! não encontramos",
        ]
        is_error = any(ind in content_text.lower() for ind in error_indicators) or any(ind in page_title.lower() for ind in error_indicators)

        if is_error:
            raise RuntimeError("página de erro ou conteúdo não encontrado")
        normalized_content = " ".join(content_text.casefold().split())
        normalized_expected = " ".join(expected_text.casefold().split())
        if normalized_expected not in normalized_content:
            # Título e URL efetivamente carregados ajudam a diferenciar
            # bloqueio do portal, navegação indesejada e alteração editorial.
            # Nunca fabricar o trecho ou salvar screenshot sem correspondência.
            raise RuntimeError(
                f"expected_text não encontrado na página: {expected_text!r}; "
                f"titulo={page_title[:100]!r}, url_final={page.url[:180]!r}, "
                f"caracteres_visiveis={len(content_text)}"
            )

        # 6. Rolar para o trecho ou elemento específico se solicitado (ex: Art. 31 da lei)
        scroll_to_text = asset.get("scroll_to_text") or expected_text
        if scroll_to_text:
            scrolled = evaluate_with_navigation_retry(page, r"""(textToFind) => {
                const normalize = text => (text || '').replace(/\s+/g, ' ').trim().toLocaleLowerCase();
                const needle = normalize(textToFind);
                let best = null;
                for (const el of document.querySelectorAll('h1, h2, h3, p, td, li, span, div, section, article, main')) {
                    if (!el.getClientRects().length) continue;
                    const text = normalize(el.innerText || el.textContent);
                    if (text.includes(needle) && (!best || text.length < best.textLength)) {
                        best = { element: el, textLength: text.length };
                    }
                }
                if (!best) return false;
                best.element.scrollIntoView({ block: 'center', inline: 'center' });
                return true;
            }""", scroll_to_text, operation_name="localizar o trecho")
            if not scrolled:
                raise RuntimeError(f"trecho esperado não foi localizado para a captura: {scroll_to_text!r}")
            print(f"[auto_capture] Rolagem até '{scroll_to_text}' realizada com sucesso.")
            page.wait_for_timeout(1000)
            wait_for_page_settle(page)

        # 7. Capture an authored region, or the complete contextual block.
        # A verified phrase somewhere on a page does not make a viewport a proof.
        target_selector = asset.get("target_selector")
        captured_element = False

        if asset.get("capture_scope") == "desktop_context":
            context_proof = capture_desktop_context(page, expected_text, target_selector, temp_path)
            captured_element = True
        elif target_selector:
            try:
                locator = page.locator(target_selector).first
                if locator.is_visible(timeout=3000):
                    unobscure_excerpt(locator)
                    locator.screenshot(path=str(temp_path))
                    captured_element = True
                    print(f"[auto_capture] Screenshot do elemento ({target_selector}) salvo com sucesso.")
            except Exception as sel_exc:
                raise RuntimeError(f"target_selector não encontrado: {target_selector}") from sel_exc
            if not captured_element:
                raise RuntimeError(f"target_selector não visível: {target_selector}")

        if not captured_element:
            selected = evaluate_with_navigation_retry(page, r"""(expected) => {
                const normalize = text => (text || '').replace(/\s+/g, ' ').trim().toLocaleLowerCase();
                const needle = normalize(expected);
                const candidates = [...document.querySelectorAll('p, li, tr, td, h1, h2, h3, blockquote, div, section, span, article, main')]
                  .filter(el => el.getClientRects().length && normalize(el.innerText).includes(needle));
                candidates.sort((a, b) => normalize(a.innerText).length - normalize(b.innerText).length);
                const target = candidates[0];
                if (!target) return false;
                // Prefer the real article's context (headline/byline/hero/lead)
                // when it fits a legible bounded screenshot. Never move or
                // synthesize text in the original publication.
                const parentArticle = target.closest('article, [itemtype*="NewsArticle"], main');
                let chosen = target;
                if (parentArticle) {
                  const valid = [];
                  for (let p = target; p && parentArticle.contains(p); p = p.parentElement) {
                    const rect = p.getBoundingClientRect();
                    if (rect.width >= 480 && rect.width <= 1320 &&
                        rect.height >= 200 && rect.height <= 1450 &&
                        normalize(p.innerText).includes(needle)) {
                      valid.push(p);
                    }
                    if (p === parentArticle) break;
                  }
                  const rich = valid.filter(el => el.querySelector('h1, h2, img, time'));
                  chosen = rich.at(-1) || valid.at(-1) || target;
                }
                chosen.setAttribute('data-ode-source-proof', 'true');
                return true;
            }""", expected_text, operation_name="selecionar o bloco de evidência")
            if not selected:
                raise RuntimeError("trecho sem bloco contextual visível; forneça target_selector")
            # Element screenshots retain the entire block, including text below
            # the viewport. Never manufacture a document from authored text.
            locator = page.locator('[data-ode-source-proof="true"]').first
            unobscure_excerpt(locator)
            locator.screenshot(path=str(temp_path))
            print(f"[auto_capture] Bloco contextual completo salvo em: {dest_path.name}")

        temp_path.replace(dest_path)
        asset["captured_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        if asset.get("capture_scope") == "desktop_context":
            temp_path.with_name(temp_path.stem + '.context.png').replace(dest_path.with_name(dest_path.stem + '.context.png'))
            provenance = {"mode": "authentic_page_capture", "source_page_url": url,
                          "expected_text": expected_text, "page_title": page_title,
                          "image_sha256": hashlib.sha256(dest_path.read_bytes()).hexdigest(),
                          "captured_at": asset["captured_at"], **context_proof}
            dest_path.with_suffix(".provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return True

    except Exception as exc:
        raise RuntimeError(f"Asset {asset.get('id')}: captura de {url} falhou: {exc}") from exc
    finally:
        temp_path.unlink(missing_ok=True)
        temp_path.with_name(temp_path.stem + '.context.png').unlink(missing_ok=True)
        if context is not None:
            context.close()


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
    for asset in excerpts:
        validate_source_asset(asset)

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
        raise RuntimeError(f"Playwright Chromium indisponível; captura interrompida: {exc}") from exc

    success_count = 0
    try:
        from news_reconstruction import render_reconstruction
        for asset in excerpts:
            try:
                if capture_asset(asset, captures_dir, browser):
                    # Preserve the authentic page, including its editorial
                    # surroundings. Do not replace successful screenshots
                    # with simulated article panels.
                    success_count += 1
            except Exception as exc:
                if asset.get("capture_sha256"):
                    raise  # Stale authored coordinates cannot target replacement pixels.
                if not asset.get("editorial_reconstruction"):
                    raise
                print(f"[auto_capture] Falha de captura ({exc}). Usando reconstrução editorial identificada.")
                render_reconstruction(asset, captures_dir, str(exc))
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
