"""Simple RBD example.

Code comments:
1.  The arrow style and font can be set by changing the value of
    `config.ARROW_STYLE` and `config.SERIF_FONT`
2.  Here, a `Group` block is made by simply multiplying a `Block` instance by an integer
3.  To group different blocks vertically and set a title and color, use the `Group` class
4.  Adding `Block` instances creates a `Series` instance
5.  To group different blocks horizontally and set a title and color, use the `Series` class
6.  Custom color `myblue` used in first block is defined here

"""

# pylint: disable=C0103
from os import path, chdir

from pyrbd import Block, Group, Series, Diagram, config

config.ARROW_STYLE = "-latex"  # (1)
config.SERIF_FONT = True

chdir(path.dirname(__file__))

# Define all the blocks in the diagram
start_block = Block("Start", "myblue", parent=None)
parallel = 2 * Block("Parallel blocks", "gray", parent=start_block)  # (2)
block_1 = Block(r"Block 1", "yellow!50")
block_2 = Block(r"Block 2", "yellow!50")
block_3 = Block(r"Block 3", "yellow!50")
block_4 = Block(r"Block 4", "yellow!50")
group = Group(  # (3)
    [block_1 + block_2, block_3 + block_4],  # (4)
    parent=parallel,
    text="Group",
    color="yellow",
)
block_a = Block(r"Block A", "orange!50")
block_b = Block(r"Block B", "orange!50")
series = Series([block_a, block_b], "Series", "orange", parent=group)  # (5)
end_block = Block("End", "green!50", parent=series)

# Add blocks to Diagram class instance and compile diagram
diag = Diagram(
    "example_RBD",
    blocks=[start_block, parallel, group, series, end_block],
    hazard="Hazard",
    colors={"myblue": "8888ff"},  # (6)
)
diag.write()
diag.compile(["svg", "png"])
