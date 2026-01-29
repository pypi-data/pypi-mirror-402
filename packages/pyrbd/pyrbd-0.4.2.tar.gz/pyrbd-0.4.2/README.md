# <img alt="pyRBDlogo" src="https://raw.githubusercontent.com/hghugdal/pyrbd/23d7f00ca74e8465df3760821488b4bb78df803c/docs/images/logo.svg" width=40 align=top> pyRBD

[![PyPI - Version](https://img.shields.io/pypi/v/pyrbd)](https://pypi.org/project/pyrbd/)
<img alt="Python" src="https://img.shields.io/badge/Python->= 3.10-blue?logo=python&link=None">
<img alt="Tests" src="https://img.shields.io/badge/Tests-Passing-darkgreen?logo=pytest&link=None">
<img alt="Coverage" src="https://img.shields.io/badge/Coverage-100%25-darkgreen?link=None">
<img alt="Pylint" src="https://img.shields.io/badge/Pylint-10%2F10-darkgreen?link=None">

A Python package for creating simple reliability block diagrams (RBDs) using `LaTeX` and [`TikZ`](https://en.wikipedia.org/wiki/PGF/TikZ).

## Dependencies
`pyRBD` requires a working installation of `LaTeX` including [`TikZ`](https://en.wikipedia.org/wiki/PGF/TikZ) and [`latexmk`](https://ctan.org/pkg/latexmk/).

## Simple example diagram
The blocks of the RBD are defined using `Block`, `Series` and `Group`, and the diagram itself is handled by the `Diagram` class. A simple example is given by the code

```python linenums="1"
from pyrbd import Block, Diagram

start_block = Block("Start", "blue!30", parent=None)
parallel = 2 * Block("Parallel blocks", "gray", parent=start_block)
end_block = Block("End", "green!50", parent=parallel)

diagram = Diagram(
    "simple_RBD",
    blocks=[start_block, parallel, end_block],
)
diagram.write()
diagram.compile()
```

producing the following diagram
<div><img src="https://raw.githubusercontent.com/hghugdal/pyrbd/e11808e9a40c902f0e1c2c2b0b42ca0d90170cd1/docs/examples/simple_RBD.svg" width=500/></div>

For more examples, visit the [documentation](https://hghugdal.github.io/pyrbd/).
