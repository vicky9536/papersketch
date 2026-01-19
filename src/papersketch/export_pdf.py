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
    # (Keep this mostly for semantic HTML; poster layout is controlled by WeasyPrint CSS below)
    html_doc = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
      </head>
      <body>
        {html_body}
      </body>
    </html>
    """

    poster_css = CSS(string="""
        @page {
            size: A2 portrait;
            margin: 12mm;
        }

        body {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 12pt;
            line-height: 1.35;
            color: #111;

            column-count: 2;
            column-gap: 12mm;
        }

        h1 {
            column-span: all;
            font-size: 26pt;
            margin: 0 0 8mm 0;
        }

        h2 {
            font-size: 16pt;
            margin: 6mm 0 3mm 0;
            font-weight: bold;
        }

        h3 {
            font-size: 13pt;
            margin: 4mm 0 2mm 0;
            font-weight: bold;
        }

        p, li {
            margin: 2mm 0;
        }

        ul, ol {
            padding-left: 5mm;
        }

        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 4mm auto;
            break-inside: avoid;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            break-inside: avoid;
            margin: 4mm 0;
            font-size: 11pt;
        }

        th, td {
            border: 0.3mm solid #ccc;
            padding: 2mm;
            vertical-align: top;
        }

        pre {
            font-size: 11pt;
            line-height: 1.3;
            break-inside: avoid;
        }

        figcaption {
            font-size: 11pt;
            text-align: center;
            margin-top: 1mm;
        }
    """)
    # Render HTML -> PDF
    pdf_bytes = HTML(string=html_doc).write_pdf(stylesheets=[poster_css])
    return pdf_bytes