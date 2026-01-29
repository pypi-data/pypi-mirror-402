"""Tests for `Diagram` class."""

from os import chdir
from typing import Generator

import pytest
from pytest import FixtureRequest

from pyrbd import Diagram, Block, config, Group, Series


@pytest.fixture(name="arrow_style", scope="module", params=["", "-latex"])
def arrow_style_fixture(request: FixtureRequest) -> Generator[str, None, None]:
    """Arrow style pytest fixture."""

    styles: str = request.param

    yield styles


@pytest.fixture(name="diagram")
def diagram_fixture(arrow_style: str) -> Diagram:
    """Diagram pytest fixture."""

    config.ARROW_STYLE = arrow_style

    start_block = Block("Start", "myblue", parent=None)
    parallel = 2 * Block("Parallel blocks", "gray", parent=start_block)
    group = Group(
        [
            Block(r"Block 1", "yellow!50") + Block(r"Block 2", "yellow!50"),
            Block(r"Block 3", "yellow!50")
            + Block(r"Block 4", "yellow!50")
            + Block(r"Block 5", "yellow!50"),
        ],
        parent=parallel,
        text="Group",
        color="yellow",
    )
    series = Series(
        [Block(r"Block A", "orange!50"), Block(r"Block B", "orange!50")],
        "Series",
        "orange",
        parent=group,
    )
    end_block = Block("End", "green!50", parent=series)

    return Diagram(
        "test_diagram",
        [start_block, parallel, group, series, end_block],
        "Fire",
        colors={"myblue": "8888ff"},
    )


def test_diagram_init(diagram: Diagram) -> None:
    """Test __init__ of `Diagram` class."""

    assert diagram.filename == "test_diagram"
    assert "myblue" in diagram.colors.keys()
    assert isinstance(diagram.head, Block)


def test_diagram_wo_hazard() -> None:
    """Test __init__ of `Diagram` class without `hazard` specified."""

    head = Block("block1", "white")
    blocks = [head, Block("block2", "blue"), Block("block3", "green")]
    diagram = Diagram("test_diagram", blocks)

    # When hazard is not specified, blocks[0] is set as head of diagram
    assert diagram.head is head
    assert len(diagram.blocks) == 2


def test_diagram_write(tmp_path, diagram: Diagram) -> None:
    """Test `Diagram` `write` method."""

    temp_dir = tmp_path / "test_diagram"
    temp_dir.mkdir()

    chdir(temp_dir)

    diagram.write()

    tmp_file = temp_dir / f"{diagram.filename}.tex"

    for hex_code in diagram.colors.values():
        assert hex_code in tmp_file.read_text()
    assert config.ARROW_STYLE in tmp_file.read_text()
    assert diagram.head.text in tmp_file.read_text()
