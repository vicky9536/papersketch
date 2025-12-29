# src/papersketch/tools.py

from __future__ import annotations

import os
import glob
from typing import TypedDict, Optional, Any

from mcp.server.fastmcp import FastMCP
from .client import PaperSketchClient

# MCP server object
mcp = FastMCP("papersketch-server")

# Reuse one client instance
_client = PaperSketchClient()


class PaperSketchResult(TypedDict, total=False):
    summary: str
    version: Optional[str]
    modelInfo: Optional[str]


# -----------------------------
# Apps SDK UI Widget Resource
# -----------------------------
WIDGET_URI = "ui://papersketch/inline-card"

def _repo_root() -> str:
    # src/papersketch/tools.py -> repo root is ../../..
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def _load_ui_bundle() -> tuple[str, str]:
    """
    Load the Vite build output from ui/dist/assets.
    Requires: (cd ui && npm run build)
    """
    root = _repo_root()
    assets_dir = os.path.join(root, "ui", "dist", "assets")

    js_files = sorted(glob.glob(os.path.join(assets_dir, "*.js")))
    css_files = sorted(glob.glob(os.path.join(assets_dir, "*.css")))

    if not js_files:
        raise RuntimeError(
            f"No UI bundle found in {assets_dir}. Run `cd ui && npm run build` first."
        )

    with open(js_files[0], "r", encoding="utf-8") as f:
        js_text = f.read()

    css_text = ""
    if css_files:
        with open(css_files[0], "r", encoding="utf-8") as f:
            css_text = f.read()

    return js_text, css_text


@mcp.resource(WIDGET_URI)
def papersketch_inline_widget() -> dict[str, Any]:
    """
    IMPORTANT:
    - Must return a resource with mimeType: text/html+skybridge
    - ChatGPT loads this in an iframe and injects window.openai.toolOutput
    """
    js_text, css_text = _load_ui_bundle()

    html = f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <style>{css_text}</style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module">
{js_text}
    </script>
  </body>
</html>
"""

    return {
        "contents": [
            {
                "uri": WIDGET_URI,
                "mimeType": "text/html+skybridge",
                "text": html,
                "_meta": {
                    # Optional: allow the widget to load images from your API host
                    # (Your canvas composer may try to fetch images from scholar.club)
                    "openai/widgetCSP": {
                        "resource_domains": [
                            "https://scholar.club",
                            "https://arxiv.org",
                        ],
                        "connect_domains": [
                            "https://scholar.club",
                            "https://arxiv.org",
                        ],
                    }
                },
            }
        ]
    }


# -----------------------------
# Tool
# -----------------------------
@mcp.tool(
    annotations={
        "openai": {
            "outputTemplate": WIDGET_URI,
            "toolInvocation": {
                "invoking": "Generating PaperSketch…",
                "invoked": "PaperSketch ready",
            },
        }
    }
)
def summarize_paper(url: str, lang: str = "en") -> PaperSketchResult:
    """
    Summarize an academic PDF from a public URL using the Papersketch API.

    - url: Public URL to a PDF (e.g. arXiv link).
    - lang: "en" (English) or "ch" (Chinese).
    """
    data = _client.summarize(url=url, lang=lang)

    return {
        "summary": data.get("paperSketch", "") or "",
        "version": data.get("version"),
        "modelInfo": data.get("modelInfo"),
    }
