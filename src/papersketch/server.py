# src/papersketch/server.py
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import uvicorn
from starlette.responses import Response, PlainTextResponse
from starlette.routing import Route

from .tools import mcp, cache_get_file

app = mcp.streamable_http_app()


def download_file(request):
    token = request.path_params["token"]
    item = cache_get_file(token)
    if not item:
        return PlainTextResponse("File not found or expired", status_code=404)

    file_bytes, filename, mime_type = item
    return Response(
        content=file_bytes,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


# New generic route (recommended)
app.router.routes.append(Route("/papersketch/file/{token}", download_file, methods=["GET"]))

# Backward compatibility route (if old widget still uses /papersketch/pdf/...)
app.router.routes.append(Route("/papersketch/pdf/{token}", download_file, methods=["GET"]))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
