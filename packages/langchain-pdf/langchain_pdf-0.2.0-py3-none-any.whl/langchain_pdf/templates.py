"""
templates.py
------------

High-level document templates.

A template defines HOW raw text flows through the system:
normalize → parse → render.

Templates allow future customization (themes, spacing,
different render strategies) without touching core logic.
"""

from fpdf import FPDF

from .normalizer import TextNormalizer
from .parser import BlockParser
from .renderer import PDFRenderer


class ProfessionalTemplate:
    """
    Default professional document template.

    This template produces clean, readable,
    business-style PDFs from LLM output.
    """

    def __init__(self):
        self._normalizer = TextNormalizer()
        self._parser = BlockParser()

    def render(self, pdf: FPDF, text: str) -> None:
        """
        Render text into the provided PDF instance.

        Parameters
        ----------
        pdf : FPDF
            Active PDF document.
        text : str
            Raw or semi-structured text (LLM output).
        """
        clean_text = self._normalizer.normalize(text)
        blocks = self._parser.parse(clean_text)

        renderer = PDFRenderer(pdf)
        renderer.render(blocks)
