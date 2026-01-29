# momatrix

A custom marimo widget for matrix input built with `anywidget`.

## Installation

```bash
uv add momatrix
```

## Usage

```python
import marimo as mo
from momatrix import MatrixInput, MatrixDisplay

# Create a matrix input in a marimo notebook
matrix = MatrixInput()
matrix

# Display a matrix in a marimo notebook
MatrixDisplay(matrix.value)
```

More examples can be found at "https://codeberg.org/hannesknoll/momatrix/examples".
