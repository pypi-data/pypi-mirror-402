Creating diagrams with pyRBD is done in two steps:

1. Defining the blocks of the diagram and the relationship between them.
2. Adding blocks to the diagram and compiling the output diagram.

The first step is done using the class [`Block`](block.md#pyrbd.block.Block) or child classes [`Series`](block.md#pyrbd.block.Series) and [`Group`](block.md#pyrbd.block.Group).

The second step is done using [`Diagram`](diagram.md).

Global configuration options defined in the [`config`](config.md) module.
