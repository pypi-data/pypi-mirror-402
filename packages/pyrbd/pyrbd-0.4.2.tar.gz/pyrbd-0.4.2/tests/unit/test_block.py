"""Tests for classes in block.py"""

from copy import deepcopy

import pytest

from pyrbd import Block, Series, Group


def test_block() -> None:
    """Test `Block` __init__ and properties."""

    block = Block("Block", "blue")
    tikz_node = block.get_node()
    assert "right=" not in tikz_node
    assert "\\draw" not in tikz_node

    child = Block("Child", "green", shift=(0.5, 2), parent=block)
    assert child.id == str(int(block.id) + 1)
    tikz_node = child.get_node(connector_position=0.5)
    assert f"[right=1.0cm of {block.id}, yshift=2cm]" in tikz_node
    assert (
        f"[arrowcolor, thick, rectangle connector=0.5cm] ({block.id}.east) to ({child.id}.west);"
    ) in tikz_node

    node = child.get_node()
    assert "green" in node
    assert "Child" in node


def test_series() -> None:
    """Test `Series` __init__ and properties."""

    block_1 = Block("Block 1", "blue")
    block_2 = Block("Block 2", "green")
    series = Series([block_1, block_2])

    assert series.parent is None

    assert block_1.id == f"{series.id}+0"
    assert block_2.id == f"{series.id}+1"
    assert block_1.parent is None
    assert block_2.parent is block_1

    tikz_node = series.get_node()

    assert "background" not in tikz_node
    assert "% label text" not in tikz_node

    series_node = Series([block_1, block_2], "Series label", "gray", parent=series)

    assert series_node.id == str(int(series.id) + 1)
    tikz_node = series_node.get_node()
    assert "gray" in tikz_node
    assert "gray!50" in tikz_node and "Series label" in tikz_node

    for color in ["blue", "green", "gray"]:
        assert color in series_node.get_node()


def test_group() -> None:
    """Test `Group` __init__ and properties."""

    block_1 = Block("Block 1", "blue")
    block_2 = Block("Block 2", "green")
    group = Group([block_1, block_2])

    assert group.parent is None

    tikz_node = group.get_node()

    assert "background" not in tikz_node
    assert "% label text" not in tikz_node

    assert len(group.shift) == 2
    assert group.shifts == [0, -group.shift_scale]

    assert block_1.id == f"{group.id}-0"
    assert block_2.id == f"{group.id}-1"
    assert block_1.parent is group
    assert block_2.parent is group

    group_node = Group([block_1, block_2], parent=group)
    assert group_node.id == str(int(group.id) + 1)

    for color in ["blue", "green"]:
        assert color in group_node.get_node()

    group_w_background = Group(
        [block_1, block_2], parent=group, text="Group label", color="black"
    )
    tikz_node = group_w_background.get_node()
    assert "black" in tikz_node
    assert "Group label" in tikz_node


def test_add() -> None:
    """Tests for __add__ for `Block` class."""

    block = Block("block", "white")

    assert isinstance(series := block + deepcopy(block), Series)
    assert len(series.blocks) == 2

    for variable in [2, None, False, 3.0]:
        with pytest.raises(TypeError):
            print(block + variable)  # type: ignore
        with pytest.raises(TypeError):
            print(variable + block)  # type: ignore


def test_mul_rmul() -> None:
    """Tests for __mul__ for `Block` class."""

    block = Block("block", "white")

    assert isinstance(group := 3 * block, Group)
    assert len(group.blocks) == 3

    assert isinstance(series := block * 2, Series)
    assert len(series.blocks) == 2

    assert isinstance(series * 3, Series)
    assert isinstance(3 * series, Group)
    assert isinstance(group * 3, Series)
    assert isinstance(3 * group, Group)

    for value in [-1, 0, 2.4, False]:
        with pytest.raises(ValueError):
            print(value * block)  # type: ignore
        with pytest.raises(ValueError):
            print(block * value)  # type: ignore

    rblock = 1 * block
    assert rblock is block
    assert isinstance(rblock, Block)
    lblock = block * 1
    assert lblock is block
    assert isinstance(lblock, Block)


def test_get_blocks() -> None:
    """Test get_blocks generator function."""

    block = Block("self", "black")
    assert block.get_blocks().__next__() is block

    series = block * 3
    assert list(series.get_blocks()) == series.blocks

    group = 5 * block
    assert list(group.get_blocks()) == group.blocks
