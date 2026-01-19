# src/papersketch/tools.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import time
import uuid
import os

import mcp.types as types
from mcp.server.fastmcp import FastMCP

from .client import PaperSketchClient
from .export_image import markdown_to_png_bytes

TOOL_NAME = "summarize_paper"
WIDGET_TEMPLATE_URI = "ui://widget/papersketch-inline.html"
WIDGET_TITLE = "PaperSketch summary"
WIDGET_INVOKING = "Generating PaperSketch…"
WIDGET_INVOKED = "PaperSketch ready"
MIME_TYPE = "text/html+skybridge"

# IMPORTANT: stateless for multi-client (Inspector + GPT)
mcp = FastMCP(name="papersketch", stateless_http=True)

_client = PaperSketchClient()

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
WIDGET_HTML_PATH = ASSETS_DIR / "papersketch-inline.html"

# -----------------------------
# File cache (in-memory)
# token -> (file_bytes, filename, mime_type, expires_at_epoch)
# -----------------------------
_FILE_CACHE: Dict[str, Tuple[bytes, str, str, float]] = {}
_FILE_TTL_SECONDS = 15 * 60  # 15 minutes


def log(msg: str) -> None:
    print(f"[PAPERSKETCH MCP] {msg}", flush=True)


def _cache_put_file(file_bytes: bytes, filename: str, mime_type: str) -> str:
    token = uuid.uuid4().hex
    _FILE_CACHE[token] = (file_bytes, filename, mime_type, time.time() + _FILE_TTL_SECONDS)
    return token


def cache_get_file(token: str) -> Optional[Tuple[bytes, str, str]]:
    """
    Exported for server.py route to retrieve cached files.
    Returns (file_bytes, filename, mime_type) if present and not expired, else None.
    """
    item = _FILE_CACHE.get(token)
    if not item:
        return None
    file_bytes, filename, mime_type, expires_at = item
    if time.time() > expires_at:
        _FILE_CACHE.pop(token, None)
        return None
    return file_bytes, filename, mime_type


def _cache_cleanup_expired() -> None:
    now = time.time()
    expired = [k for k, (_, __, ___, exp) in _FILE_CACHE.items() if exp < now]
    for k in expired:
        _FILE_CACHE.pop(k, None)


def _load_widget_html() -> str:
    log("Loading widget HTML")
    if WIDGET_HTML_PATH.exists():
        html = WIDGET_HTML_PATH.read_text(encoding="utf8")
        log(f"Widget HTML loaded ({len(html)} bytes)")
        return html
    raise FileNotFoundError(f"Widget HTML not found at {WIDGET_HTML_PATH}")


PAPERSKETCH_WIDGET_HTML = _load_widget_html()


def _widget_meta() -> Dict[str, Any]:
    return {
        "openai/outputTemplate": WIDGET_TEMPLATE_URI,
        "openai/toolInvocation/invoking": WIDGET_INVOKING,
        "openai/toolInvocation/invoked": WIDGET_INVOKED,
        "openai/widgetAccessible": True,
    }


# --- Tool schema ---
TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "url": {"type": "string"},
        "lang": {"type": "string", "enum": ["en", "ch"], "default": "en"},
    },
    "required": ["url"],
    "additionalProperties": False,
}


@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    log("list_tools called")
    return [
        types.Tool(
            name=TOOL_NAME,
            title="Summarize paper",
            description="Summarize an academic PDF and render a PaperSketch inline card.",
            inputSchema=TOOL_INPUT_SCHEMA,
            _meta=_widget_meta(),
        )
    ]


@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    log("list_resources called")
    return [
        types.Resource(
            name=WIDGET_TITLE,
            title=WIDGET_TITLE,
            uri=WIDGET_TEMPLATE_URI,
            description="PaperSketch widget",
            mimeType=MIME_TYPE,
            _meta=_widget_meta(),
        )
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    log(f"READ_RESOURCE start: {req.params.uri}")

    if str(req.params.uri) != WIDGET_TEMPLATE_URI:
        log("READ_RESOURCE unknown URI")
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    contents = [
        types.TextResourceContents(
            uri=WIDGET_TEMPLATE_URI,
            mimeType=MIME_TYPE,
            text=PAPERSKETCH_WIDGET_HTML,
            _meta=_widget_meta(),
        )
    ]

    log("READ_RESOURCE done")
    return types.ServerResult(types.ReadResourceResult(contents=contents))


async def _handle_call_tool(req: types.CallToolRequest) -> types.ServerResult:
    log(f"CALL_TOOL start: {req.params.name}")

    if req.params.name != TOOL_NAME:
        log("CALL_TOOL unknown tool")
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Unknown tool: {req.params.name}")],
                isError=True,
            )
        )

    args = req.params.arguments or {}
    url = args.get("url")
    lang = args.get("lang", "en")

    if not url or not isinstance(url, str):
        log("CALL_TOOL invalid args")
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text="Missing required argument: url")],
                isError=True,
            )
        )

    # Clean expired cache entries occasionally
    _cache_cleanup_expired()

    # 1) Call PaperSketch API
    log(f"CALL_TOOL invoking PaperSketch API: {url}")
    t0 = time.time()
    data = _client.summarize(url=url, lang=lang)
    log(f"CALL_TOOL PaperSketch API returned in {time.time() - t0:.2f}s")

    raw_summary = (
        data.get("paperSketch")
        or data.get("summary")
        or data.get("paper_sketch")
        or ""
    )

    # 2) Generate PNG and return a small URL token (NOT base64)
    image_filename = "paper_sketch.png"
    image_url = ""

    if raw_summary:
        try:
            t1 = time.time()

            # Tune these for your preferred look:
            # - width_px ~ 1000-1400 usually good
            # - device_scale_factor 2.0 = crisp text
            png_bytes = await markdown_to_png_bytes(raw_summary, width_px=1200, device_scale_factor=2.0)

            token = _cache_put_file(png_bytes, image_filename, "image/png")

            base = os.environ.get("PAPERSKETCH_PUBLIC_BASE_URL", "").rstrip("/")
            if base:
                image_url = f"{base}/papersketch/file/{token}"
            else:
                # Fallback for local dev (will NOT work inside ChatGPT widget)
                image_url = f"/papersketch/file/{token}"

            log(
                f"PNG generated+cached in {time.time() - t1:.2f}s "
                f"(token={token}, {len(png_bytes)} bytes)"
            )
        except Exception as e:
            # Don’t fail the whole tool if export fails; still return the summary.
            log(f"Image generation failed: {e}")

    structured_content = {
        "summary": raw_summary,
        "version": data.get("version"),
        "modelInfo": data.get("modelInfo"),
        "imageUrl": image_url,
        "imageFilename": image_filename,

        # Backward compatibility: if your widget still expects pdfUrl, point it to the image.
        "pdfUrl": image_url,
        "pdfFilename": image_filename,
    }

    meta = _widget_meta()

    log("CALL_TOOL done, returning result")
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text="PaperSketch generated.")],
            structuredContent=structured_content,
            _meta=meta,
        )
    )


# Wire handlers
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource
mcp._mcp_server.request_handlers[types.CallToolRequest] = _handle_call_tool
