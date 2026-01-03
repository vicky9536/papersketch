"""
PDF export utility for PaperSketch

Converts a Markdown summary (with remote image URLs)
into a single downloadable PDF.
"""

from markdown import markdown
from weasyprint import HTML, CSS


def markdown_to_pdf_bytes(markdown_text: str) -> bytes:
    """
    Convert Markdown text (with embedded image URLs) to PDF bytes.

    Args:
        markdown_text (str): Markdown-formatted summary text

    Returns:
        bytes: PDF file bytes
    """

    # Convert Markdown -> HTML body
    html_body = markdown(
        markdown_text,
        extensions=[
            "tables",
            "fenced_code",
            "sane_lists",
        ],
    )

    # Wrap in a minimal HTML document
    html_doc = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          body {{
            font-family: Arial, Helvetica, sans-serif;
            font-size: 12pt;
            line-height: 1.5;
            color: #111;
          }}

          h1, h2, h3 {{
            margin-top: 24px;
            margin-bottom: 12px;
          }}

          p {{
            margin: 8px 0;
          }}

          ul, ol {{
            margin-left: 24px;
          }}

          img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 14px auto;
          }}

          code {{
            background: #f5f5f5;
            padding: 2px 4px;
            font-size: 0.95em;
          }}

          pre {{
            background: #f5f5f5;
            padding: 10px;
            overflow-wrap: break-word;
            white-space: pre-wrap;
          }}
        </style>
      </head>
      <body>
        {html_body}
      </body>
    </html>
    """

    # Render HTML -> PDF
    pdf_bytes = HTML(string=html_doc).write_pdf(
        stylesheets=[
            CSS(string="""
                @page {
                    size: A4;
                    margin: 18mm;
                }
            """)
        ]
    )

    return pdf_bytes
