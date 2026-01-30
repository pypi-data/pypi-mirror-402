"""
exporter.py
-----------

Public API for exporting documents.

This module defines the main entry point
that users of the library interact with.
"""

from .base import BasePDF
from pathlib import Path

from .templates import ProfessionalTemplate


def export_pdf(
    text: str,
    output_path: str | Path,
    *,
    title: str | None = None
) -> None:
    """
    Export text into a PDF file.

    Parameters
    ----------
    text : str
        Raw or LLM-generated text.
    output_path : str | Path
        Destination PDF file path.
    title : str | None, optional
        Optional document title.
    """
    pdf = BasePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()

    if title:
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 10, title, ln=True)
        pdf.ln(5)

    template = ProfessionalTemplate()
    template.render(pdf, text)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
