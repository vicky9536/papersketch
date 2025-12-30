# src/papersketch/server.py
from __future__ import annotations

import uvicorn
from .tools import mcp

app = mcp.streamable_http_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
