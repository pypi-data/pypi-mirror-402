"""
blocks.py
---------

Defines the semantic building blocks of a document.

This module acts as a lightweight Document AST (Abstract Syntax Tree),
allowing LLM output to be converted into structured content before
rendering (PDF, DOCX, HTML, etc.).

Keeping structure separate from rendering ensures:
- Deterministic layouts
- Renderer-agnostic design
- Easier testing and extension
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Block:
    """
    Base class for all document blocks.

    Attributes
    ----------
    text : str
        The textual content of the block.
    """
    text: str


@dataclass(frozen=True)
class Heading(Block):
    """
    Represents a document heading.

    Attributes
    ----------
    level : int
        Heading level (1 = largest, 3 = smallest).
    """
    level: Literal[1, 2, 3]


@dataclass(frozen=True)
class Paragraph(Block):
    """
    Represents a standard paragraph of text.
    """
    pass


@dataclass(frozen=True)
class Bullet(Block):
    """
    Represents a bullet/list item.
    """
    pass
