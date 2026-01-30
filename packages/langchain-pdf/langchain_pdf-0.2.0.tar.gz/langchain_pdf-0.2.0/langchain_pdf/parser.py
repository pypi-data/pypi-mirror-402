"""
parser.py
---------

Converts normalized text into semantic document blocks.

This module is intentionally simple and deterministic.
It does not attempt to infer structure beyond explicitly
supported syntax.
"""

from typing import List
from .blocks import Block, Heading, Paragraph, Bullet


class BlockParser:
    """
    Parses normalized text into a list of semantic blocks.

    Supported syntax:
    - Headings: #, ##, ###
    - Bullets: -
    - Paragraphs: default
    """

    def parse(self, text: str) -> List[Block]:
        """
        Parse normalized text into document blocks.

        Parameters
        ----------
        text : str
            Normalized text (output of TextNormalizer).

        Returns
        -------
        List[Block]
            Ordered list of semantic document blocks.
        """
        if not text:
            return []

        blocks: List[Block] = []

        for line in text.splitlines():
            line = line.strip()

            if not line:
                # Explicitly skip empty lines
                continue

            block = self._parse_line(line)
            if block:
                blocks.append(block)

        return blocks

    # -------------------------
    # Internal helpers
    # -------------------------

    def _parse_line(self, line: str) -> Block:
        """
        Parse a single line into a Block.
        """
        if line.startswith("### "):
            return Heading(text=line[4:], level=3)

        if line.startswith("## "):
            return Heading(text=line[3:], level=2)

        if line.startswith("# "):
            return Heading(text=line[2:], level=1)

        if line == "-" or line.strip() == "":
            return None

        if line.startswith("- "):
            return Bullet(text=line[2:])

        return Paragraph(text=line)
