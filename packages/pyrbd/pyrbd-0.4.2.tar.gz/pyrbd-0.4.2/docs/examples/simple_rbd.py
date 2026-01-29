"""Simple RBD example.

Annotations:
1.  The first block does not need a parent
2.  To get identical parallel blocks, multiply a `Block` instance by an `int`
3.  For the other blocks we must specify the previous block in the diagram as the parent block
4.  We can specify multiple output formats by providing a list of formats.
    Defaults to PDF if unspecified.
"""

# pylint: disable=C0103
from os import path, chdir

from pyrbd import Block, Diagram

chdir(path.dirname(__file__))

# Define the blocks comprising the diagram
start_block = Block("Start", "blue!30")  # (1)
parallel = 2 * Block("Parallel blocks", "gray", parent=start_block)  # (2)
end_block = Block("End", "green!50", parent=parallel)  # (3)

# Define and compile the diagram
diagram = Diagram(
    "simple_RBD",
    blocks=[start_block, parallel, end_block],
)
diagram.write()
diagram.compile(["pdf", "svg"])  # (4)
