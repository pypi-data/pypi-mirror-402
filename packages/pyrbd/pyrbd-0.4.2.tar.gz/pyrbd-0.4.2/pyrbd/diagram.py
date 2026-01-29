"""Module containing Diagram class definition."""

from typing import Optional
import subprocess

import pymupdf

from . import config
from .templates import JINJA_ENV
from .block import Block


class Diagram:
    """Reliability block diagram class definition.

    Parameters
    ----------
    name : str
        name of diagram
    blocks : list[Block]
        list of `Block` instances
    hazard : str, default=""
        string defining the `hazard` block text (optional)
    colors : Optional[dict[str, str]], default=None
        dictionary with custom color definitions in HEX format:
        `{'color name': '6 digit hex code'}`

    Attributes
    ----------
    colors : dict[str, str], default={"arrowcolor": "4c4d4c", "hazardcolor": "ff6666"}
        default diagram color definitions
    """

    _template: str = "diagram.tex.jinja"
    colors: dict[str, str] = {"arrowcolor": "4c4d4c", "hazardcolor": "ff6666"}

    def __init__(
        self,
        name: str,
        blocks: list[Block],
        hazard: str = "",
        colors: Optional[dict[str, str]] = None,
    ) -> None:
        self.filename = name
        if hazard:
            self.head = Block(hazard, "hazardcolor")
        else:
            self.head = blocks.pop(0)

        self.head.id = "0"
        self.blocks = blocks
        self.blocks[0].parent = self.head

        if colors is not None:
            self.colors = self.colors | colors

    def write(self) -> None:
        """Write diagram to .tex file."""

        environment = JINJA_ENV
        template = environment.get_template(self._template)

        context = {
            "serif_font": config.SERIF_FONT,
            "arrow_style": config.ARROW_STYLE,
            "color_defs": [
                {"name": name, "hex_code": code} for name, code in self.colors.items()
            ],
            "blocks": list(block.get_node() for block in [self.head, *self.blocks]),
        }
        content = template.render(context)

        with open(f"{self.filename}.tex", mode="w", encoding="utf-8") as file:
            file.write(content)

    def _to_svg(self) -> str:
        """Convert diagram file from pdf to svg.

        Returns
        -------
        str
            filename of .svg file
        """

        pdf_document = pymupdf.open(f"{self.filename}.pdf")
        page = pdf_document[0]

        # Get and convert page to svg image
        svg_content = page.get_svg_image().splitlines()
        svg_content.insert(
            1,
            "\n".join(
                [
                    "<style>",
                    "   @media (prefers-color-scheme: light) { :root { --color: #000000; } }",
                    "   @media (prefers-color-scheme: dark) { :root { --color: #DDDDDD; } }",
                    "</style>",
                ]
            ),
        )
        svg_content = "\n".join(svg_content).replace(r"#4c4d4c", "var(--color)")

        # Save to file
        with open(output_file := f"{self.filename}.svg", "w", encoding="utf-8") as file:
            file.write(svg_content)

        pdf_document.close()

        return output_file

    def _to_png(self) -> str:
        """Convert diagram file from pdf to png.

        Returns
        -------
        str
            filename of .png file
        """

        pdf_document = pymupdf.open(f"{self.filename}.pdf")
        page = pdf_document[0]

        # Get image
        image = page.get_pixmap(dpi=300)

        # Save to file
        image.save(output_file := f"{self.filename}.png")

        pdf_document.close()

        return output_file

    def compile(
        self, output: str | list[str] = "pdf", clear_source: bool = True
    ) -> list[str]:
        """Compile diagram .tex file.

        Parameters
        ----------
        output : str | list[str], default='pdf'
            output format string or list of output formats for diagram. Valid output formats are

            - `'pdf'` (default)
            - `'svg'`
            - `'png'`

        clear_source : bool, default=True
            .tex source file is deleted after compilation if `True`

        Returns
        -------
        list[str]
            list of output filenames

        Raises
        ------
        FileNotFoundError
            If .tex file is not found, e.g. because `Diagram.write()` has not been called
            before `Diagram.compile()`.
        """

        try:
            subprocess.check_call(
                ["latexmk", "--lualatex", f"{self.filename}.tex", "--silent"]
            )
            subprocess.check_call(["latexmk", "-c", f"{self.filename}.tex"])
            if clear_source:
                subprocess.check_call(["rm", f"{self.filename}.tex"])
        except subprocess.CalledProcessError as err:
            if err.returncode == 11:
                raise FileNotFoundError(
                    (
                        f"File {self.filename} not found. "
                        + "Check if call to Class method write() is missing."
                    )
                ) from err

        output_files: list[str] = []

        if not isinstance(output, list):
            output = [output]

        if "svg" in output:
            output_files.append(self._to_svg())
        if "png" in output:
            output_files.append(self._to_png())
        if "pdf" not in output:
            subprocess.check_call(["rm", f"{self.filename}.pdf"])
        else:
            output_files.append(f"{self.filename}.pdf")

        return output_files
