"""
renderer.py
-----------

Responsible for rendering semantic document blocks into a PDF.

This renderer uses a "Reading Theme" optimized for long-form content:
- Soft spacing
- Clear hierarchy
- Comfortable line height
- Subtle section separators
"""

from typing import Iterable
from .blocks import Block, Heading, Paragraph, Bullet
from .base import BasePDF
class ReadingTheme:
    """
    Typography and spacing configuration for readable documents.
    """
    BODY_FONT_SIZE = 10.5
    BODY_LINE_HEIGHT = 6.2

    H1_SIZE = 17
    H2_SIZE = 14
    H3_SIZE = 12

    HEADING_LINE_FACTOR = 0.56

    SPACE_BEFORE_HEADING = 2
    SPACE_AFTER_HEADING = 1.5

    BULLET_LINE_HEIGHT = 6.2
    SPACE_AFTER_BULLET_GROUP = 1.5

    SEPARATOR_COLOR = (210, 210, 210)
    SEPARATOR_THICKNESS = 0.25
    SEPARATOR_MARGIN = 2


class PDFRenderer:
    """
    Renders document blocks into a PDF using BasePDF
    and a reading-optimized theme.
    """

    def __init__(self, pdf: BasePDF):
        self.pdf = pdf
        self.theme = ReadingTheme()
        self.content_width = pdf.w - pdf.l_margin - pdf.r_margin

    def render(self, blocks: Iterable[Block]) -> None:
        for block in blocks:
            if isinstance(block, Heading):
                self._render_heading(block)

                # Separator only for non-H1
                if block.level != 1:
                    self._ensure_space(required_height=8)
                    self._render_separator()

            elif isinstance(block, Bullet):
                self._render_bullet(block)

            elif isinstance(block, Paragraph):
                self._render_paragraph(block)
    # -------------------------
    # Block renderers
    # -------------------------

    def _render_heading(self, block: Heading) -> None:
        # Ensure enough space for heading + separator + content
        self._ensure_space(required_height=35)

        size_map = {
            1: self.theme.H1_SIZE,
            2: self.theme.H2_SIZE,
            3: self.theme.H3_SIZE,
        }
        font_size = size_map.get(block.level, self.theme.H3_SIZE)

        self.pdf.ln(self.theme.SPACE_BEFORE_HEADING)
        self.pdf.set_heading_font(font_size)

        self.pdf.multi_cell(
            self.content_width,
            font_size * self.theme.HEADING_LINE_FACTOR,
            block.text
        )

        self.pdf.ln(self.theme.SPACE_AFTER_HEADING)


    def _render_paragraph(self, block: Paragraph) -> None:
        self.pdf.set_body_font(self.theme.BODY_FONT_SIZE)

        self.pdf.multi_cell(
            self.content_width,
            self.theme.BODY_LINE_HEIGHT,
            block.text
        )

        self.pdf.ln(2)

    def _render_bullet(self, block: Bullet) -> None:
        bullet_indent = 6
        text_indent = 12
        line_height = self.theme.BULLET_LINE_HEIGHT

        # Estimate bullet height conservatively
        estimated_height = line_height * 2

        # Ensure space BEFORE rendering anything
        self._ensure_space(estimated_height)

        x_start = self.pdf.get_x()
        y_start = self.pdf.get_y()

        self.pdf.set_body_font(self.theme.BODY_FONT_SIZE)

        # Bullet symbol
        self.pdf.set_xy(x_start, y_start)
        self.pdf.cell(bullet_indent, line_height, "•", align="R")

        # Bullet text
        self.pdf.set_xy(x_start + text_indent, y_start)
        self.pdf.multi_cell(
            self.content_width - text_indent,
            line_height,
            block.text
        )

        self.pdf.ln(self.theme.SPACE_AFTER_BULLET_GROUP)

    # -------------------------
    # Visual helpers
    # -------------------------

    def _render_separator(self) -> None:
        """
        Draw a subtle horizontal separator after major sections.
        """
        self.pdf.set_draw_color(*self.theme.SEPARATOR_COLOR)
        self.pdf.set_line_width(self.theme.SEPARATOR_THICKNESS)

        y = self.pdf.get_y()
        self.pdf.line(
            self.pdf.l_margin + 5,
            y,
            self.pdf.w - self.pdf.r_margin - 5,
            y
        )

        self.pdf.ln(self.theme.SEPARATOR_MARGIN)

    def _ensure_space(self, required_height: float) -> None:
        """
        Ensure there is enough space on the current page.
        If not, start a new page.
        """
        remaining = self.pdf.h - self.pdf.get_y() - self.pdf.b_margin
        if remaining < required_height:
            self.pdf.add_page()
            return True
        return False
