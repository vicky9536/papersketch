# src/papersketch/tools.py

from typing import TypedDict, Optional
from mcp.server.fastmcp import FastMCP
from client import PaperSketchClient

# MCP server object
mcp = FastMCP("papersketch-server")
# mcp = FastMCP(
#     "papersketch-server",
#     stateless_http=True,
# )

# Reuse one client instance
_client = PaperSketchClient()


class PaperSketchResult(TypedDict, total=False):
    summary: str
    version: Optional[str]
    modelInfo: Optional[str]


@mcp.tool()
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
