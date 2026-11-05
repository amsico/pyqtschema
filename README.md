# pyqtschema

`pyqtschema` allows the generation of a graphical representation of a [jsonschema](https://json-schema.org/). A given
schema is translated to QWidgets.

## Installation

As usual:
* install the pypi version

  `pip install pyqtschema`

* or clone the repository

  `pip install git+https://github.com/amsico/pyqtschema.git`

`pyqtschema` uses [QtPy](https://pypi.org/project/QtPy/) to support any Qt binding
(PyQt5, PyQt6, PySide2, PySide6). The binding itself is **not** installed
automatically, so install one of your choice:

```
pip install pyqtschema[pyside6]     # PySide6
pip install pyqtschema[pyqt5]       # PyQt5
pip install pyqtschema[pyqt6]       # PyQt6
pip install pyqtschema[pyside2]     # PySide2
```

or install a binding directly, e.g. `pip install PySide6`.

By default QtPy prefers PyQt5 when several bindings are installed; you can control
this via the `QT_API` environment variable.

## Usage

Use the `WidgetBuilder` in applications or run the module to visualize a schema:

`python -m pyqtschema ./path/to/your/scheam.json`

## Examples

Several examples are available in the [examples](https://github.com/amsico/pyqtschema/tree/main/examples) folder. The
examples use [pydantic](https://pydantic-docs.helpmanual.io/) to generate schemas easily.

## Background

`pyqtschema` is inspired by [qt-jsonschema-form](https://github.com/agoose77/qt-jsonschema-form). Due to the author's
lack of [time](https://github.com/agoose77/qt-jsonschema-form/pull/1#issuecomment-595491242) and the missing
[anyOf-support](https://github.com/agoose77/qt-jsonschema-form/blob/ca71ddbf10c2b309c3eb9c4fda6b054a0cb573dd/README.md?plain=1#L10)
, this project was started.
