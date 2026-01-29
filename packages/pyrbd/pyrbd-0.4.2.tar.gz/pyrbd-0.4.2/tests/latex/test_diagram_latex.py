"""Tests for `Diagram` class."""

from os import chdir

import pytest

from pyrbd import Diagram, Block


@pytest.fixture(name="diagram")
def diagram_fixture() -> Diagram:
    """Diagram pytest fixture."""

    block1 = Block("block1", "white")
    block2 = Block("block2", "white")
    block3 = Block("block3", "white")
    return Diagram("test_diagram_compile", [block1, block2, block3], "Overpressure")


def test_diagram_compile(tmp_path, diagram: Diagram) -> None:
    """Test `Diagram` `write` method."""

    temp_dir = tmp_path / "test_diagram_compile"
    temp_dir.mkdir()
    chdir(temp_dir)

    with pytest.raises(FileNotFoundError):
        diagram.compile()

    diagram.write()
    assert ".pdf" in "\n".join(diagram.compile(clear_source=False))
    assert ".svg" in "\n".join(diagram.compile("svg", clear_source=False))
    assert ".png" in "\n".join(diagram.compile("png", clear_source=False))
    assert ".pdf" not in "\n".join(diagram.compile(["svg", "png"], clear_source=False))
    assert ".pdf" in "\n".join(diagram.compile(["pdf", "svg"]))
