"""
normalizer.py
-------------

Canonicalizes raw LLM output into a stable, document-safe format.

Goal:
- Remove ALL markdown & visual noise
- Preserve semantic meaning only
- Produce deterministic, parser-friendly text

This normalizer is intentionally opinionated.
"""

import re
from typing import List


class TextNormalizer:
    # ---------- public API ----------

    def normalize(self, text: str) -> str:
        if not text or not text.strip():
            return ""

        text = text.replace("\r\n", "\n").strip()

        # Stage 1: Global destructive cleanup
        text = self._remove_code_blocks(text)
        text = self._remove_markdown_emphasis(text)
        text = self._remove_visual_separators(text)

        # Stage 2: Line-level canonicalization
        lines = text.split("\n")
        lines = self._normalize_lines(lines)

        # Stage 3: Structural cleanup
        lines = self._remove_duplicate_titles(lines)
        lines = self._remove_orphan_bullets(lines)

        # Stage 4: Final whitespace normalization
        text = "\n".join(lines)
        text = self._normalize_whitespace(text)

        return text.strip()

    # ---------- stage 1 ----------

    def _remove_code_blocks(self, text: str) -> str:
        """Remove fenced and inline code blocks entirely."""
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"`([^`]*)`", r"\1", text)
        return text

    def _remove_markdown_emphasis(self, text: str) -> str:
        """Strip all markdown emphasis symbols."""
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"__(.*?)__", r"\1", text)
        text = re.sub(r"\*(.*?)\*", r"\1", text)
        text = re.sub(r"_(.*?)_", r"\1", text)
        return text

    def _remove_visual_separators(self, text: str) -> str:
        """Remove visual-only separators."""
        return re.sub(r"^\s*[-–—_=]{2,}\s*$", "", text, flags=re.MULTILINE)

    # ---------- stage 2 ----------

    def _normalize_lines(self, lines: List[str]) -> List[str]:
        """
        Convert every line into one of:
        - heading
        - bullet
        - paragraph
        """
        normalized: List[str] = []

        for raw in lines:
            line = raw.strip()
            if not line:
                normalized.append("")
                continue

            # Headings
            if line.startswith("###"):
                normalized.append("### " + line.lstrip("#").strip())
                continue

            if line.startswith("##"):
                normalized.append("## " + line.lstrip("#").strip())
                continue

            if line.startswith("#"):
                normalized.append("# " + line.lstrip("#").strip())
                continue

            # Numbered lists → bullets
            if re.match(r"\d+[\.\)]\s+", line):
                normalized.append("- " + re.sub(r"\d+[\.\)]\s+", "", line))
                continue

            # Bullet variants
            if re.match(r"^[•*\-+]\s+", line):
                normalized.append("- " + re.sub(r"^[•*\-+]\s+", "", line))
                continue

            # Hashtags (keep as paragraph, not bullet)
            if line.startswith("#") and " " not in line:
                normalized.append(line)
                continue

            # Default: paragraph
            normalized.append(line)

        return normalized

    # ---------- stage 3 ----------

    def _remove_duplicate_titles(self, lines: List[str]) -> List[str]:
        """Keep only the first H1 title."""
        seen_h1 = False
        result: List[str] = []

        for line in lines:
            if line.startswith("# "):
                if seen_h1:
                    continue
                seen_h1 = True
            result.append(line)

        return result

    def _remove_orphan_bullets(self, lines: List[str]) -> List[str]:
        """
        Remove bullets that have no meaningful content.
        """
        result: List[str] = []

        for line in lines:
            if line.strip() == "-" or line.strip() == "•":
                continue
            result.append(line)

        return result

    # ---------- stage 4 ----------

    def _normalize_whitespace(self, text: str) -> str:
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text
