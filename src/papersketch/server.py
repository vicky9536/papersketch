# src/papersketch/server.py
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import uvicorn
from starlette.responses import Response, PlainTextResponse
from starlette.routing import Route

from .tools import mcp, cache_get_pdf

app = mcp.streamable_http_app()


def download_pdf(request):
    token = request.path_params["token"]
    item = cache_get_pdf(token)
    if not item:
        return PlainTextResponse("PDF not found or expired", status_code=404)

    pdf_bytes, filename = item
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


# Register the route on the underlying Starlette router
app.router.routes.append(Route("/papersketch/pdf/{token}", download_pdf, methods=["GET"]))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
