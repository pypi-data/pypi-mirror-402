"""Module containing Block, Series and Group class definitions."""

from typing import Optional, Generator, overload, Literal
from copy import deepcopy
from collections import namedtuple
import itertools

from .templates import JINJA_ENV

Padding = namedtuple("Padding", ["n", "e", "s", "w"])


class Block:
    """Block entering a reliability block diagram.

    Parameters
    ----------
    text : str
        block text string
    color : str
        block color
    parent : Optional["Block"], default=None
        parent `Block` instance
    shift : tuple[float, float], default=(0.0, 0.0)
        additional position shift `(x, y)` relative to `parent` `Block` instance

    Attributes
    ----------
    node_options : str
        TikZ node formatting options
    arrow_options : str, default="arrowcolor, thick"
        TikZ arrow formatting options
    arrow_length : float, default=0.5
        default arrow length between nodes (in cm)
    """

    _template = "block.tex.jinja"
    node_options: str = ", ".join(
        [
            "anchor=west",
            "align=center",
            "fill={fill_color}",
            "draw=black!70!gray",
            "minimum height=1cm",
            "rounded corners=0.3mm",
            "inner sep=4pt",
            "outer sep=0pt",
        ]
    )

    arrow_options: str = "arrowcolor, thick"
    arrow_length: float = 0.5

    _block_count = itertools.count(start=1)

    def __init__(
        self,
        text: str,
        color: str,
        parent: Optional["Block"] = None,
        shift: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        self.text = text
        self.color = color
        self.parent = parent
        self.shift = shift
        self.last = self
        self.id = str(next(self._block_count))

    def get_node(self, connector_position: Optional[float] = None) -> str:
        """Get TikZ node string.

        Parameters
        ----------
        connector_position : Optional[float], default=None
            distance in cm to right angle bend in connector. Defaults to `0.5*arrow_length`.

        Returns
        -------
        str
            TikZ string for rendering block
        """

        if connector_position is None:
            connector_position = self.arrow_length / 2

        environment = JINJA_ENV
        template = environment.get_template(self._template)
        context = {
            "type": "Block",
            "block": self,
            "node_options": self.node_options.format(fill_color=self.color),
            "connector_position": connector_position,
        }

        return template.render(context)

    def get_blocks(self) -> Generator["Block", None, None]:
        """Yield child `Block` istances."""

        yield self

    def __add__(self, block: "Block") -> "Series":
        """Add two `Block` instances to make a `Series` instance.

        Parameters
        ----------
        block : Block
            another `Block` instance

        Returns
        -------
        Series
            `Series` instance with `blocks = [self, block]`

        Raises
        ------
        TypeError
            If `block` is not an instance of `Block`
        """

        if not isinstance(block, Block):
            raise TypeError(
                f"Cannot add object of type {type(block)=} to Block instance."
            )

        return Series([self, block], parent=self.parent)

    @overload
    def __rmul__(self, value: Literal[1]) -> "Block": ...

    @overload
    def __rmul__(self, value: int) -> "Group": ...

    def __rmul__(self, value: int) -> "Group | Block":
        """Right multiply `Block` instance by `value` to make `Group` with repeated blocks.

        Parameters
        ----------
        value : int
            multiplicative factor, a positive integer

        Returns
        -------
        Group | Block
            `Group` instance with `value` copies of block if `value > 1`, `self` otherwise

        Raises
        ------
        ValueError
            If `value` is not a positive integer
        """

        if not isinstance(value, int) or value <= 0:
            raise ValueError("Multiplicative factor `value` must be a positive integer")

        if value == 1:
            return self

        blocks: list[Block] = [deepcopy(self) for _ in range(value)]

        return Group(blocks, parent=self.parent)

    @overload
    def __mul__(self, value: Literal[1]) -> "Block": ...

    @overload
    def __mul__(self, value: int) -> "Series": ...

    def __mul__(self, value: int) -> "Series | Block":
        """Multiply `Block` instance by `value` to make `Series` with repeated blocks.

        Parameters
        ----------
        value : int
            multiplicative factor, a positive integer

        Returns
        -------
        Series | Block
            `Series` instance with `value` copies of block if `value > 1`, self otherwise

        Raises
        ------
        ValueError
            If `value` is not a positive integer
        """

        if not isinstance(value, int) or value <= 0:
            raise ValueError("Multiplicative factor `value` must be a positive integer")

        if value == 1:
            return self

        blocks: list[Block] = [deepcopy(self) for _ in range(value)]

        return Series(blocks, parent=self.parent)


class Series(Block):
    """Series configuration of `Block` instances for horisontal grouping.

    Parameters
    ----------
    blocks : list[Block]
        list of `Block` instances
    text: str, default=""
        series label text
    color: str, default="white"
        series color, defaults to white
    parent : Optional[Block], default=None
        parent `Block` instance

    Attributes
    ----------
    node_options : str
        TikZ node options
    internal_arrow_length : float, default=0.3
        distance between blocks in series
    pad : Padding, default=Padding(1, 1, 1, 2.5)
        `namedtuple` `(north, east, south, west)` defining padding (in mmm) between
        blocks and series frame
    label_height : float, default=5.0
        height of series label (in mm)

    """

    _template = "series.tex.jinja"
    node_options: str = ", ".join(
        [
            "anchor=west",
            "align=center",
            "inner sep=0pt",
            "outer sep=0pt",
        ]
    )
    internal_arrow_length: float = 0.3
    pad: Padding = Padding(1, 1, 1, 2.5)
    label_height: float = 5.0

    def __init__(
        self,
        blocks: list[Block],
        text: str = "",
        color: str = "white",
        parent: Optional[Block] = None,
    ) -> None:
        Block.__init__(self, text, color, parent)

        self.blocks = blocks
        self.last = self.blocks[-1]

        self.blocks[0].id = f"{self.id}+0"
        for i, (block, new_parent) in enumerate(
            zip(self.blocks[1::], self.blocks[0:-1]), start=1
        ):
            block.parent = new_parent
            block.id = f"{self.id}+{i}"
            if not isinstance(block, Series):
                block.arrow_length = self.internal_arrow_length

        if True in [isinstance(block, Series) for block in self.blocks]:
            self.shift = (0, 0.25)

    def get_node(self, connector_position: Optional[float] = None) -> str:
        """Get TikZ node string.

        Parameters
        ----------
        connector_position : Optional[float], default=None
            distance in cm to right angle bend in connector. Defaults to `0.5 * arrow_length`

        Returns
        -------
        str
            TikZ string for rendering series

        """
        if connector_position is None:
            connector_position = self.arrow_length / 2

        block_nodes = [block.get_node(connector_position) for block in self.blocks]

        environment = JINJA_ENV
        template = environment.get_template(self._template)
        context = {
            "type": "Series",
            "block": self,
            "node_options": self.node_options,
            "connector_position": connector_position,
            "pad": self.pad,
            "block_nodes": block_nodes,
            "first": self.blocks[0],
        }

        return template.render(context)

    def get_blocks(self) -> Generator[Block, None, None]:
        yield from [
            children for block in self.blocks for children in block.get_blocks()
        ]


class Group(Block):
    """Group of `Block` instances for vertical stacking.

    Parameters
    ----------
    blocks : list[Block]
        list of `Block` instances
    text : str, default=""
        group label text
    color : str, default=""
        group color, defaults to white
    parent : Optional[Block], default=None
        parent `Block` instance

    Attributes
    ----------
    shift_scale : float, default=1.2
        scaling factor for vertical shifts of blocks
    node_options : str
        TikZ node options
    internal_arrow_length : float, default=0.3
        distance between blocks in series
    end_arrow_scaling : float, default=0.75
        scale factor of last arrow in `Group`
    pad : Padding, default=Padding(1, 1, 1, 1)
        `namedtuple` `(north, east, south, west)` defining padding (in mmm) between
        blocks and series frame
    label_height : float, default=5.0
        height of series label (in mm)
    """

    _template = "group.tex.jinja"
    shift_scale: float = 1.2
    node_options: str = ", ".join(
        [
            "anchor=west",
            "align=center",
            "inner sep=0pt",
            "outer sep=0pt",
        ]
    )
    internal_arrow_length: float = 0.3
    end_arrow_scaling: float = 0.75
    pad: Padding = Padding(1, 1, 1, 1)
    label_height: float = 5.0

    def __init__(
        self,
        blocks: list[Block],
        text: str = "",
        color: str = "",
        parent: Optional[Block] = None,
    ) -> None:
        Block.__init__(self, text, color, parent)

        self.blocks = blocks
        for i, (block, shift) in enumerate(zip(self.blocks, self.shifts)):
            block.shift = (0, shift)
            block.parent = self
            block.id = f"{self.id}-{i}"
            block.arrow_length = self.internal_arrow_length

    @property
    def shifts(self) -> list[float]:
        """List of vertical position shifts for each `Block` instance in group.

        Returns
        -------
        list[float]
            list of vertical position shifts for each `Block` instance in group
        """

        n_blocks = len(self.blocks)

        return list(-self.shift_scale * n for n in range(n_blocks))

    @property
    def sorted_blocks(self) -> list[Block]:
        """Get TikZ string for arrow connecting stacked blocks."""

        # scaling = 0.75

        series_blocks = [block for block in self.blocks if isinstance(block, Series)]
        series_blocks.sort(
            key=lambda block: len(list(block.get_blocks())), reverse=True
        )

        if len(series_blocks) > 0:
            longest_series_index = self.blocks.index(series_blocks[0])
        else:
            longest_series_index = 0
        blocks = deepcopy(self.blocks)
        longest_series = blocks.pop(longest_series_index)

        return [longest_series, *blocks]

    def get_node(self, connector_position: Optional[float] = None) -> str:
        """Get TikZ node string.

        Parameters
        ----------
        connector_position : Optional[float], default=None
            distance in cm to right angle bend in connector.
            Locked to 0.0 for `Group` class

        Returns
        -------
        str
            TikZ string for rendering group
        """

        connector_position = 0.0

        block_nodes = [block.get_node(connector_position) for block in self.blocks]

        environment = JINJA_ENV
        template = environment.get_template(self._template)
        context = {
            "type": "Group",
            "block": self,
            "node_options": self.node_options,
            "connector_position": connector_position,
            "pad": self.pad,
            "block_nodes": block_nodes,
        }

        return template.render(context)

    def get_blocks(self) -> Generator[Block, None, None]:
        yield from self.blocks
