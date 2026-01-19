# src/papersketch/export_image.py
from __future__ import annotations

import html as _html
import re
from typing import List, Tuple

from markdown import markdown


# Matches markdown list markers like "-", "*", "•" (optionally preceded by whitespace)
_BULLET_RE = re.compile(r"^\s*(?:[-*•])\s+(.*)\s*$", re.UNICODE)


def _strip_bullet(line: str) -> str:
    m = _BULLET_RE.match(line)
    return m.group(1).strip() if m else line.strip()


def _is_field_line(line: str, field_name: str) -> bool:
    """
    Detects:
      - Paper Title:
      - Author Information:
      - Institutional Information:
    on lines that may be plain text or markdown bullets.
    """
    s = _strip_bullet(line).lower()
    return s.startswith(f"{field_name.lower()}:")  # e.g. "paper title:"


def _field_value_after_colon(line: str) -> str:
    s = _strip_bullet(line)
    return s.split(":", 1)[1].strip() if ":" in s else ""


def _is_list_item(line: str) -> bool:
    """
    A list item can be:
      - "- foo"
      - "* foo"
      - "• foo"
      - "1. foo"
      - "2) foo"
    """
    if _BULLET_RE.match(line):
        return True
    s = line.strip()
    return bool(re.match(r"^\d+\s*[.)]\s+.+$", s))


def _extract_title_authors_institutions(md: str) -> Tuple[str, str, str, str]:
    """
    Extracts a fixed header:
      - title
      - authors (can be inline or a block list)
      - institutions (can be inline or a block list)

    Returns (title, authors_html, institutions_html, remaining_markdown).
    """
    lines = md.strip().splitlines()

    title = ""
    authors: List[str] = []
    insts: List[str] = []

    remaining: List[str] = []

    mode = None  # None | "authors" | "insts"

    for raw in lines:
        line = raw.rstrip("\n")

        # Detect start of fields
        if _is_field_line(line, "Paper Title"):
            title = _field_value_after_colon(line)
            mode = None
            continue

        if _is_field_line(line, "Author Information"):
            v = _field_value_after_colon(line)
            if v:
                # inline authors
                authors = [v]
                mode = None
            else:
                # block authors lines follow
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

        # If we are inside authors/institutions block, capture list items until a blank line
        # or until we hit another field line / a non-list paragraph.
        if mode in ("authors", "insts"):
            if not line.strip():
                mode = None
                continue

            # Stop block if another field header appears
            if (
                _is_field_line(line, "Paper Title")
                or _is_field_line(line, "Author Information")
                or _is_field_line(line, "Institutional Information")
            ):
                mode = None
                remaining.append(raw)
                continue

            if _is_list_item(line):
                item = _strip_bullet(line)
                # Strip leading "1. " / "1) "
                item = re.sub(r"^\d+\s*[.)]\s+", "", item).strip()
                if item:
                    (authors if mode == "authors" else insts).append(item)
                continue

            # If not a list item, treat it as part of the block anyway (some models output plain lines)
            txt = line.strip()
            if txt:
                (authors if mode == "authors" else insts).append(txt)
                continue

        # Otherwise, keep as remaining markdown
        remaining.append(raw)

    # Build header HTML
    authors_html = ""
    if authors:
        # If there is one big inline string, keep it; otherwise join cleanly.
        if len(authors) == 1:
            authors_html = _html.escape(authors[0])
        else:
            authors_html = ", ".join(_html.escape(a) for a in authors)

    institutions_html = ""
    if insts:
        lis = "\n".join(f"<li>{_html.escape(x)}</li>" for x in insts if x)
        institutions_html = f"<ul class='paper-inst'>{lis}</ul>"

    return title.strip(), authors_html, institutions_html, "\n".join(remaining).strip()


async def markdown_to_png_bytes(
    markdown_text: str,
    *,
    width_px: int = 1200,
    device_scale_factor: float = 2.0,
) -> bytes:
    """
    Convert Markdown -> HTML -> PNG bytes via Playwright (async).
    Produces a single tall PNG (no pagination) and a fixed-format header.
    """
    title, authors_html, institutions_html, remaining_md = _extract_title_authors_institutions(markdown_text)

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

    html_doc = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    :root {{
      --text: #111;
      --muted: #444;
      --border: #e3e3e3;
      --bg: #fff;
    }}
    html, body {{
      background: var(--bg);
      margin: 0;
      padding: 0;
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, Helvetica, sans-serif;
    }}

    .page {{
      width: {width_px}px;
      margin: 0 auto;
      padding: 32px 28px;
      box-sizing: border-box;
    }}

    /* HEADER: make it unmistakably large + bold */
    .paper-header {{
      margin: 0 0 26px 0;
      padding: 0 0 16px 0;
      border-bottom: 3px solid var(--border);
    }}
    .paper-title {{
      font-size: 56px;
      font-weight: 900;
      line-height: 1.08;
      margin: 0 0 12px 0;
      letter-spacing: -0.6px;
    }}
    .paper-authors {{
      font-size: 22px;
      font-weight: 800;
      line-height: 1.35;
      color: #222;
      margin: 0 0 10px 0;
    }}
    .paper-inst {{
      list-style: none;
      padding: 0;
      margin: 0;
      color: #555;
      font-size: 14px;
      line-height: 1.35;
    }}
    .paper-inst li {{
      margin: 2px 0;
    }}

    /* two-column content like your sample */
    .content {{
      column-count: 2;
      column-gap: 28px;
    }}

    h1 {{
      column-span: all;
      font-size: 30px;
      line-height: 1.15;
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
      margin: 6px 0;
    }}

    img {{
      max-width: 100%;
      height: auto;
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
      vertical-align: top;
    }}
    th {{
      background: #f6f6f6;
      font-weight: 700;
    }}

    code {{
      background: #f5f5f5;
      padding: 1px 4px;
      border-radius: 4px;
      font-size: 0.95em;
    }}
    pre {{
      background: #f5f5f5;
      padding: 10px 12px;
      border-radius: 8px;
      white-space: pre-wrap;
      overflow-wrap: break-word;
      break-inside: avoid;
      font-size: 13px;
      line-height: 1.35;
    }}

    blockquote, pre, table, img {{
      break-inside: avoid;
    }}
  </style>
</head>
<body>
  <div class="page">
    {header_html}
    <div class="content">
      {body_html}
    </div>
  </div>
</body>
</html>
"""

    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        raise RuntimeError(
            "Playwright is not installed. Install with:\n"
            "  uv add playwright\n"
            "  playwright install chromium\n"
        ) from e

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            page = await browser.new_page(
                viewport={"width": width_px, "height": 900},
                device_scale_factor=device_scale_factor,
            )

            await page.set_content(html_doc, wait_until="load")

            # wait for images to load (don’t hang forever)
            try:
                await page.wait_for_function(
                    """
                    () => {
                      const imgs = Array.from(document.images || []);
                      if (imgs.length === 0) return true;
                      return imgs.every(img => img.complete && img.naturalWidth > 0);
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