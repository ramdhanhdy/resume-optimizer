"""Renderer Agent - Zero-cost PDF/DOCX generation from optimized resume."""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, cast
from jinja2 import Environment, FileSystemLoader, select_autoescape
from xhtml2pdf import pisa
import io

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


class RendererAgent:
    """
    Zero-cost rendering agent for producing PDF/DOCX from optimized resume data.
    Two modes:
      1) 'text' mode -> wraps your optimized resume (string) nicely.
      2) 'structured' mode -> uses schema-aware HTML (closer to professional format).
    """

    def __init__(self):
        """Initialize the renderer with Jinja2 template environment."""
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def to_pdf_from_text(self, optimized_resume_text: str) -> bytes:
        """Quick win: produce a clean single-column PDF from plain text.

        Args:
            optimized_resume_text: The optimized resume as plain text

        Returns:
            PDF file as bytes
        """
        tpl = self.env.get_template("resume_basic.html")
        html = tpl.render(text=optimized_resume_text)
        return self._html_to_pdf(html)

    def to_pdf_from_structured(self, data: Dict[str, Any]) -> bytes:
        """Pixel-match template using structured fields (name, sections, etc.).

        Args:
            data: Structured resume data with sections

        Returns:
            PDF file as bytes
        """
        tpl = self.env.get_template("resume_structured.html")
        html = tpl.render(**data)
        return self._html_to_pdf(html)

    def to_pdf_from_html(self, html: str) -> bytes:
        """Convert HTML string directly to PDF.

        Args:
            html: Complete HTML document as string

        Returns:
            PDF file as bytes
        """
        return self._html_to_pdf(html)

    def _html_to_pdf(self, html: str) -> bytes:
        """Convert HTML string to PDF bytes using xhtml2pdf.

        Args:
            html: HTML content as string

        Returns:
            PDF file as bytes
        """
        output = io.BytesIO()
        pisa_status = cast(Any, pisa.CreatePDF(html, dest=output))
        if pisa_status.err:
            raise RuntimeError(
                f"PDF generation failed with error code: {pisa_status.err}"
            )
        output.seek(0)
        return output.read()

    def to_docx_from_structured(self, data: Dict[str, Any]) -> bytes:
        """Optional: generate an editable DOCX via docxtpl template.

        Args:
            data: Structured resume data with sections

        Returns:
            DOCX file as bytes
        """
        from docxtpl import DocxTemplate
        import io

        template_path = TEMPLATES_DIR / "resume_structured.docx"
        if not template_path.exists():
            raise FileNotFoundError(
                f"DOCX template not found at {template_path}. "
                "Please create a template file to use this feature."
            )

        doc = DocxTemplate(str(template_path))
        doc.render(data)

        # Return as bytes
        out = io.BytesIO()
        doc.save(out)
        out.seek(0)
        return out.read()
