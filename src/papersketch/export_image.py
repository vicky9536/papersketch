# src/papersketch/export_image.py
from __future__ import annotations

import base64
import html as _html
import re
from pathlib import Path
from typing import List, Tuple

from markdown import markdown


# -----------------------------
# Utilities for parsing header
# -----------------------------

_BULLET_RE = re.compile(r"^\s*(?:[-*•])\s+(.*)\s*$", re.UNICODE)


def _strip_bullet(line: str) -> str:
    m = _BULLET_RE.match(line)
    return m.group(1).strip() if m else line.strip()


def _is_field_line(line: str, field_name: str) -> bool:
    s = _strip_bullet(line).lower()
    return s.startswith(f"{field_name.lower()}:")


def _field_value_after_colon(line: str) -> str:
    s = _strip_bullet(line)
    return s.split(":", 1)[1].strip() if ":" in s else ""


def _is_list_item(line: str) -> bool:
    if _BULLET_RE.match(line):
        return True
    return bool(re.match(r"^\s*\d+\s*[.)]\s+.+$", line))


def _extract_title_authors_institutions(
    md: str,
) -> Tuple[str, str, str, str]:
    """
    Extracts:
      - Paper Title
      - Author Information (inline or list)
      - Institutional Information (list)
    Returns:
      (title, authors_html, institutions_html, remaining_markdown)
    """
    lines = md.strip().splitlines()

    title = ""
    authors: List[str] = []
    insts: List[str] = []

    remaining: List[str] = []
    mode = None  # None | "authors" | "insts"

    for raw in lines:
        line = raw.rstrip("\n")

        if _is_field_line(line, "Paper Title"):
            title = _field_value_after_colon(line)
            mode = None
            continue

        if _is_field_line(line, "Author Information"):
            v = _field_value_after_colon(line)
            if v:
                authors = [v]
                mode = None
            else:
                authors = []
                mode = "authors"
            continue

        if _is_field_line(line, "Institutional Information"):
            v = _field_value_after_colon(line)
            if v:
                insts = [v]
                mode = None
            else:
                insts = []
                mode = "insts"
            continue

        if mode in ("authors", "insts"):
            if not line.strip():
                mode = None
                continue

            if _is_list_item(line):
                item = _strip_bullet(line)
                item = re.sub(r"^\d+\s*[.)]\s+", "", item).strip()
                if item:
                    (authors if mode == "authors" else insts).append(item)
                continue

            txt = line.strip()
            if txt:
                (authors if mode == "authors" else insts).append(txt)
                continue

        remaining.append(raw)

    authors_html = ", ".join(_html.escape(a) for a in authors) if authors else ""

    institutions_html = ""
    if insts:
        lis = "\n".join(f"<li>{_html.escape(x)}</li>" for x in insts)
        institutions_html = f"<ul class='paper-inst'>{lis}</ul>"

    return title.strip(), authors_html, institutions_html, "\n".join(remaining).strip()


# -----------------------------
# Asset loading (logo)
# -----------------------------

def _load_asset_data_url(filename: str) -> str:
    assets_dir = Path(__file__).resolve().parent / "assets"
    p = assets_dir / filename
    data = p.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")

    ext = p.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


# -----------------------------
# Main exporter
# -----------------------------

async def markdown_to_png_bytes(
    markdown_text: str,
    *,
    width_px: int = 1200,
    device_scale_factor: float = 2.0,
) -> bytes:
    """
    Render PaperSketch markdown into a single tall PNG.
    Includes:
      - Fixed large title + author header
      - Two-column content
      - All figures
      - Scholar logo footer
    """

    title, authors_html, institutions_html, remaining_md = (
        _extract_title_authors_institutions(markdown_text)
    )

    body_html = markdown(
        remaining_md,
        extensions=["tables", "fenced_code", "sane_lists"],
    )

    header_html = ""
    if title or authors_html or institutions_html:
        header_html = f"""
        <header class="paper-header">
          {f'<div class="paper-title">{_html.escape(title)}</div>' if title else ''}
          {f'<div class="paper-authors">{authors_html}</div>' if authors_html else ''}
          {institutions_html if institutions_html else ''}
        </header>
        """

    logo_data_url = _load_asset_data_url("scholarLogo.png")
    footer_html = f"""
    <footer class="sketch-footer">
      <img class="sketch-logo" src="{logo_data_url}" alt="Scholar logo" />
    </footer>
    """

    html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
:root {{
  --text: #111;
  --muted: #444;
  --border: #e3e3e3;
}}

html, body {{
  margin: 0;
  padding: 0;
  background: #fff;
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, Helvetica, sans-serif;
}}

.page {{
  width: {width_px}px;
  margin: 0 auto;
  padding: 32px 28px;
  box-sizing: border-box;
}}

.paper-header {{
  margin-bottom: 26px;
  padding-bottom: 16px;
  border-bottom: 3px solid var(--border);
}}

.paper-title {{
  font-size: 56px;
  font-weight: 900;
  line-height: 1.08;
  margin-bottom: 12px;
}}

.paper-authors {{
  font-size: 22px;
  font-weight: 800;
  line-height: 1.35;
  color: #222;
  margin-bottom: 10px;
}}

.paper-inst {{
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 14px;
  color: #555;
}}

.paper-inst li {{
  margin: 2px 0;
}}

.content {{
  column-count: 2;
  column-gap: 28px;
}}

h1 {{
  column-span: all;
  font-size: 30px;
  margin: 0 0 14px 0;
  font-weight: 850;
}}

h2 {{
  font-size: 20px;
  margin: 18px 0 8px 0;
  font-weight: 800;
}}

h3 {{
  font-size: 16px;
  margin: 12px 0 6px 0;
  font-weight: 800;
}}

p, li {{
  font-size: 14px;
  line-height: 1.45;
  margin: 6px 0;
}}

ul, ol {{
  padding-left: 18px;
}}

img {{
  max-width: 100%;
  display: block;
  margin: 10px auto;
  break-inside: avoid;
}}

table {{
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0;
  break-inside: avoid;
  font-size: 13px;
}}

th, td {{
  border: 1px solid #ddd;
  padding: 6px 8px;
}}

pre {{
  background: #f5f5f5;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
  break-inside: avoid;
}}

.sketch-footer {{
  margin-top: 28px;
  padding-top: 14px;
  border-top: 2px solid #eee;
  text-align: center;
}}

.sketch-logo {{
  height: 38px;
  width: auto;
}}
</style>
</head>
<body>
  <div class="page">
    {header_html}
    <div class="content">
      {body_html}
    </div>
    {footer_html}
  </div>
</body>
</html>
"""

    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        raise RuntimeError(
            "Playwright not installed. Run:\n"
            "  uv add playwright\n"
            "  playwright install chromium"
        ) from e

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            page = await browser.new_page(
                viewport={"width": width_px, "height": 900},
                device_scale_factor=device_scale_factor,
            )
            await page.set_content(html_doc, wait_until="load")

            # Wait for all images (figures + logo)
            try:
                await page.wait_for_function(
                    """
                    () => {
                      const imgs = Array.from(document.images || []);
                      if (!imgs.length) return true;
                      return imgs.every(i => i.complete && i.naturalWidth > 0);
                    }
                    """,
                    timeout=8000,
                )
            except Exception:
                pass

            await page.wait_for_timeout(200)
            return await page.screenshot(full_page=True, type="png")
        finally:
            await browser.close()