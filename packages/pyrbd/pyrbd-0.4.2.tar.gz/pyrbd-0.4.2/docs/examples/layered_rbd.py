"""Example with layered Series and Group instances."""

from os import path, chdir
from copy import deepcopy

from pyrbd import Block, Group, Series, Diagram

chdir(path.dirname(__file__))

# Define the blocks comprising the diagram
start_block = Block("Start", "blue!30")
block = Block("Block", "gray!20")
group_1 = Group(
    [b * 2 for b in 3 * [block]],
    text="Group with Series",
    color="orange",
    parent=start_block,
)
series_1 = Series(
    [deepcopy(block), 2 * block],
    text="Series with Group",
    color="red",
    parent=group_1,
)
series_2 = Series(
    [2 * block, deepcopy(block), 3 * (block * 2)],
    text="Series with mixed Groups",
    color="RoyalBlue",
    parent=series_1,
)
group_2 = Group(
    [
        block * 3,
        deepcopy(block),
        block * 4,
    ],
    text="Group with mixed Series",
    color="red",
    parent=series_2,
)
series_in_series = Series(
    [
        Series([deepcopy(block), deepcopy(block)], color="yellow", text="Child 1"),
        Series([deepcopy(block), deepcopy(block)], color="orange", text="Child 2"),
        deepcopy(block),
    ],
    parent=group_2,
    text="Parent series",
    color="red",
)
end_block = Block("End", "green!50", parent=series_in_series)

# Define and compile the diagram
diagram = Diagram(
    "layered_RBD",
    blocks=[
        start_block,
        group_1,
        series_1,
        series_2,
        group_2,
        series_in_series,
        end_block,
    ],
)
diagram.write()
diagram.compile(["pdf", "svg"])
