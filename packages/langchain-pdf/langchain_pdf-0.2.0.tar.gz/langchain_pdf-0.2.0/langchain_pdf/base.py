from fpdf import FPDF
from importlib.resources import files

class BasePDF(FPDF):
    """
    Base PDF with soft, readable typography using Inter.
    Fonts are loaded as package assets (PyPI-safe).
    """

    FONT_FAMILY = "Inter"

    def __init__(self):
        super().__init__()
        self._register_fonts()

    def _register_fonts(self):
        """
        Register Inter fonts bundled inside the package.
        """
        font_dir = files("langchain_pdf").joinpath("assets/fonts")

        regular_font = font_dir / "Inter_18pt-Regular.ttf"
        bold_font = font_dir / "Inter_18pt-Bold.ttf"

        self.add_font(
            self.FONT_FAMILY,
            "",
            str(regular_font),
            uni=True
        )

        self.add_font(
            self.FONT_FAMILY,
            "B",
            str(bold_font),
            uni=True
        )

    def set_body_font(self, size: float = 11):
        self.set_font(self.FONT_FAMILY, "", size)

    def set_heading_font(self, size: float):
        self.set_font(self.FONT_FAMILY, "B", size)
