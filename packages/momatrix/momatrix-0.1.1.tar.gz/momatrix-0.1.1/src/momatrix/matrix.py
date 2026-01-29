import anywidget
import traitlets
import pathlib
import numpy as np
import marimo as mo


class MatrixWidget(anywidget.AnyWidget):
    _esm = pathlib.Path(__file__).parent / "static" / "matrix.js"
    _css = pathlib.Path(__file__).parent / "static" / "matrix.css"

    # Synced traits
    rows = traitlets.Int(2).tag(sync=True)
    cols = traitlets.Int(2).tag(sync=True)
    _data = traitlets.List(traitlets.List(traitlets.Float())).tag(sync=True)
    style = traitlets.Unicode("").tag(sync=True)

    def __init__(self, value=None, rows=None, cols=None, style="pmatrix", **kwargs):
        # Initialize default _data before super().__init__ triggers observers
        if value is not None:
            arr = np.array(value, dtype=float)
            if rows is None:
                rows = arr.shape[0]
            if cols is None:
                cols = arr.shape[1] if len(arr.shape) > 1 else 1
            # Resize/Copy logic will happen in setter or below
        else:
            rows = rows if rows is not None else 2
            cols = cols if cols is not None else 2
            arr = np.zeros((rows, cols), dtype=float)

        kwargs["rows"] = rows
        kwargs["cols"] = cols
        kwargs["style"] = style

        # Convert numpy to list of lists for JSON serialization
        kwargs["_data"] = arr.tolist()

        super().__init__(**kwargs)

    @traitlets.observe("rows", "cols")
    def _on_dim_change(self, change):
        """Resizes internal data when dimensions change, preserving old values."""
        new_rows = self.rows
        new_cols = self.cols
        old_data = self._data

        # Create new zero matrix
        new_arr = np.zeros((new_rows, new_cols), dtype=float)

        # Copy existing data
        # We convert old_data (list of lists) to numpy for easy slicing
        if old_data:
            try:
                # Handle potentially jagged lists if manual editing happened (unlikely but safe)
                # or just standard list of lists
                old_arr = np.array(old_data)

                # Determine slice ranges
                r_lim = min(new_rows, old_arr.shape[0])
                c_lim = min(new_cols, old_arr.shape[1]) if len(old_arr.shape) > 1 else 0

                if r_lim > 0 and c_lim > 0:
                    new_arr[:r_lim, :c_lim] = old_arr[:r_lim, :c_lim]
            except Exception:
                # If conversion fails, we just keep zeros (fallback)
                pass

        self._data = new_arr.tolist()

    @property
    def value(self):
        """Returns the matrix as a numpy array."""
        return np.array(self._data, dtype=float)

    @value.setter
    def value(self, new_val):
        """Sets the matrix from a numpy array or list."""
        arr = np.array(new_val, dtype=float)
        if len(arr.shape) != 2:
            raise ValueError("Value must be a 2D array/list")

        # Updating these triggers the observers, but we want to set _data atomically
        # to match the new value exactly, not resize the old one.
        # So we update _data first, or rely on the final state.

        # Actually, simpler: just update everything.
        # The frontend will re-render.
        self.rows = arr.shape[0]
        self.cols = arr.shape[1]
        self._data = arr.tolist()


class MatrixInput(mo.ui.anywidget):
    """
    A reactive matrix input widget for marimo.
    """

    def __init__(self, value=None, rows=None, cols=None, style="pmatrix", **kwargs):
        widget = MatrixWidget(value=value, rows=rows, cols=cols, style=style, **kwargs)
        super().__init__(widget)

    @property
    def value(self):
        """Returns the matrix as a numpy array."""
        # Type ignore because self.widget is typed as AnyWidget but we know it is MatrixWidget
        return self.widget.value  # type: ignore

    @value.setter
    def value(self, value):
        self.widget.value = value  # type: ignore


class MatrixDisplay:
    """
    Displays a matrix using LaTeX math formulas in marimo.
    """

    def __init__(self, data, style="pmatrix", inline=True):
        self._data = np.array(data)
        valid_styles = {"matrix", "pmatrix", "bmatrix", "Bmatrix", "vmatrix", "Vmatrix"}
        if style not in valid_styles:
            raise ValueError(f"Invalid style '{style}'. Must be one of {valid_styles}")
        self._style = style
        self._inline = inline

    def __str__(self):
        return self._latex()

    def _latex(self):
        """Returns the LaTeX representation of the matrix."""
        if self._data.ndim == 1:
            rows_str = [" & ".join(map(str, self._data))]
        else:
            rows_str = []
            for row in self._data:
                rows_str.append(" & ".join(map(str, row)))

        content = r" \\ ".join(rows_str)
        latex = f"\\begin{{{self._style}}} {content} \\end{{{self._style}}}"

        if self._inline:
            return f"${latex}$"
        return f"$$ {latex} $$"

    def _display_(self):
        """Returns the matrix as a marimo markdown object with LaTeX."""
        return mo.md(self._latex())
