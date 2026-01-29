"""Templates subpackage."""

from os.path import abspath, join, dirname
from jinja2 import Environment, FileSystemLoader, StrictUndefined

_TEMPLATE_DIR = abspath(join(dirname(__file__), "templates/"))
JINJA_ENV: Environment = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    block_start_string=r"\BLOCK{",
    block_end_string=r"}",
    variable_start_string=r"\VAR{",
    variable_end_string=r"}",
    comment_start_string=r"\#{",
    comment_end_string=r"}",
    line_statement_prefix=r"%%",
    line_comment_prefix=r"%#",
    trim_blocks=True,
    autoescape=False,
    keep_trailing_newline=True,
    undefined=StrictUndefined,
)
