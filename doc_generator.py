"""
tools/doc_generator.py
─────────────────────────────────────────────────────────────
Saves agent output to disk in the requested format.

Supported formats:
  markdown → .md  (always works, no extra deps)
  html     → .html (wraps content in a clean template)
  pdf      → .pdf  (requires weasyprint — optional)

Usage:
  from tools.doc_generator import save
  path = save(content, filename="proposal", fmt="markdown")
"""

from __future__ import annotations
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# ── HTML shell template ────────────────────────────────────────────────
_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: 'Segoe UI', system-ui, sans-serif;
      max-width: 860px;
      margin: 48px auto;
      padding: 0 24px;
      color: #1a1a2e;
      line-height: 1.7;
    }}
    h1 {{ font-size: 2rem; color: #16213e; border-bottom: 3px solid #0f3460; padding-bottom: 8px; }}
    h2 {{ font-size: 1.4rem; color: #0f3460; margin-top: 2rem; }}
    h3 {{ font-size: 1.1rem; color: #533483; }}
    a  {{ color: #0f3460; }}
    code, pre {{
      background: #f4f4f8;
      border-radius: 4px;
      font-family: 'Fira Code', 'Consolas', monospace;
      font-size: 0.9em;
    }}
    pre  {{ padding: 16px; overflow-x: auto; }}
    code {{ padding: 2px 6px; }}
    blockquote {{
      border-left: 4px solid #0f3460;
      margin: 0;
      padding: 8px 16px;
      color: #555;
    }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #dde; padding: 8px 12px; text-align: left; }}
    th {{ background: #0f3460; color: #fff; }}
    tr:nth-child(even) {{ background: #f8f8fc; }}
    .meta {{
      font-size: 0.8rem;
      color: #888;
      margin-bottom: 2rem;
      border-bottom: 1px solid #eee;
      padding-bottom: 8px;
    }}
  </style>
</head>
<body>
  <div class="meta">GG Solutions · Generated {date}</div>
  {body}
</body>
</html>
"""


# ── Public API ────────────────────────────────────────────────────────

def save(
    content: str,
    filename: str = "output",
    fmt: str = "markdown",
    output_dir: str | None = None,
) -> Path:
    """
    Saves content to disk and returns the absolute Path.

    Args:
        content:    The text / HTML / Markdown string to save.
        filename:   Base filename (no extension).
        fmt:        "markdown" | "html" | "pdf"
        output_dir: Defaults to OUTPUT_DIR env var or ./output
    """
    out_dir = Path(output_dir or os.getenv("OUTPUT_DIR", "./output"))
    out_dir.mkdir(parents=True, exist_ok=True)

    if fmt == "markdown":
        return _save_markdown(content, filename, out_dir)
    elif fmt == "html":
        return _save_html(content, filename, out_dir)
    elif fmt == "pdf":
        return _save_pdf(content, filename, out_dir)
    else:
        logger.warning("Unknown format '%s' — falling back to markdown", fmt)
        return _save_markdown(content, filename, out_dir)


# ── Private helpers ───────────────────────────────────────────────────

def _save_markdown(content: str, filename: str, out_dir: Path) -> Path:
    path = out_dir / f"{filename}.md"
    path.write_text(content, encoding="utf-8")
    logger.info("[DocGenerator] Saved markdown → %s", path)
    return path


def _save_html(content: str, filename: str, out_dir: Path) -> Path:
    """
    If content looks like raw Markdown, convert it first.
    If content is already HTML, wrap it in the shell template.
    """
    if content.strip().startswith("<!DOCTYPE") or content.strip().startswith("<html"):
        # Already full HTML — save as-is
        path = out_dir / f"{filename}.html"
        path.write_text(content, encoding="utf-8")
    else:
        # Markdown → HTML via markdown library
        body = _md_to_html(content)
        html = _HTML_TEMPLATE.format(
            title=filename.replace("_", " ").title(),
            date=datetime.now().strftime("%d %b %Y"),
            body=body,
        )
        path = out_dir / f"{filename}.html"
        path.write_text(html, encoding="utf-8")

    logger.info("[DocGenerator] Saved HTML → %s", path)
    return path


def _save_pdf(content: str, filename: str, out_dir: Path) -> Path:
    """Converts Markdown → HTML → PDF using WeasyPrint."""
    try:
        from weasyprint import HTML as WeasyHTML  # optional dep
    except ImportError:
        logger.error(
            "[DocGenerator] weasyprint not installed. "
            "Run: pip install weasyprint. Falling back to HTML."
        )
        return _save_html(content, filename, out_dir)

    html_path = _save_html(content, f"_{filename}_tmp", out_dir)
    pdf_path = out_dir / f"{filename}.pdf"

    try:
        WeasyHTML(filename=str(html_path)).write_pdf(str(pdf_path))
        html_path.unlink(missing_ok=True)  # clean up temp file
        logger.info("[DocGenerator] Saved PDF → %s", pdf_path)
        return pdf_path
    except Exception as e:
        logger.error("[DocGenerator] PDF generation failed: %s", e)
        return html_path  # return the HTML as fallback


def _md_to_html(md_text: str) -> str:
    """Converts Markdown string to HTML body fragment."""
    try:
        import markdown
        return markdown.markdown(
            md_text,
            extensions=["tables", "fenced_code", "nl2br"],
        )
    except ImportError:
        # Ultra-basic fallback: wrap in <pre> if markdown lib missing
        logger.warning("[DocGenerator] markdown library not installed — using <pre> fallback")
        escaped = md_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<pre>{escaped}</pre>"
