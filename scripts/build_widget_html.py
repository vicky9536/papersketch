from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIST = REPO / "ui" / "dist"
OUT = REPO / "src" / "papersketch" / "assets" / "papersketch-inline.html"

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def main() -> None:
    index_html = read_text(DIST / "index.html")

    # Extract /assets/*.js and /assets/*.css from dist/index.html
    js_match = re.search(r'src="/assets/([^"]+\.js)"', index_html)
    css_match = re.search(r'href="/assets/([^"]+\.css)"', index_html)

    if not js_match:
        raise RuntimeError("Could not find JS bundle in dist/index.html")
    js_file = DIST / "assets" / js_match.group(1)
    if not js_file.exists():
        raise RuntimeError(f"JS file not found: {js_file}")

    css_text = ""
    if css_match:
        css_file = DIST / "assets" / css_match.group(1)
        if not css_file.exists():
            raise RuntimeError(f"CSS file not found: {css_file}")
        css_text = read_text(css_file)

    js_text = read_text(js_file)

    # Create a self-contained Skybridge widget HTML
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PaperSketch</title>
    <style>
{css_text}
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module">
{js_text}
    </script>
  </body>
</html>
"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote widget HTML: {OUT}")

if __name__ == "__main__":
    main()
