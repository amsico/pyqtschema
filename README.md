# pyqtschema

[![Tests](https://github.com/amsico/pyqtschema/actions/workflows/tests.yml/badge.svg)](https://github.com/amsico/pyqtschema/actions/workflows/tests.yml)

`pyqtschema` allows the generation of a graphical representation of a [jsonschema](https://json-schema.org/). A given
schema is translated to QWidgets.

## Installation

As usual:

* install the pypi version

  `pip install pyqtschema`

* or clone the repository

  `pip install git+https://github.com/amsico/pyqtschema.git`

`pyqtschema` uses [QtPy](https://pypi.org/project/QtPy/) to support any Qt binding (PyQt5, PyQt6, PySide2, PySide6). The
binding itself is **not** installed
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

## Testing

`pyqtschema` is built on [QtPy](https://pypi.org/project/QtPy/), so the same
test-suite runs against every supported Qt binding (PyQt5, PyQt6, PySide6).
The tests are plain [pytest](https://docs.pytest.org/) tests using
[pytest-qt](https://pytest-qt.readthedocs.io/) for the Qt event loop; they
exercise the widget-setup (schemas, state, hide/disable, ...) through the
public `pyqtschema` API and never depend on a concrete binding.

The binding for a run is selected through two environment variables that must
point to the same binding: `QT_API` for QtPy and `PYTEST_QT_API` for
pytest-qt.

### Run the test-suite

```console
pip install -r requirements_dev.txt
pytest
```

### Run against a specific binding

Linux / macOS (bash):

```bash
QT_API=pyqt6 
PYTEST_QT_API=pyqt6 
pytest
```

Windows (PowerShell):

```powershell
$env:QT_API = "pyqt6"
$env:PYTEST_QT_API = "pyqt6"
pytest
```

Windows (cmd):

```cmd
set QT_API=pyqt6
set PYTEST_QT_API=pyqt6
pytest
```

### Run against all installed bindings

```console
pytest --all-backends
```

This runs the test-suite once per installed Qt binding -- each run in its own
process -- and reports a combined result.

### Run via tox

[tox](https://tox.wiki/) runs the test-suite in isolated environments for
every supported Python version (3.11 - 3.14) and Qt binding:

```console
pip install tox
tox
```

or a single combination:

```console
tox -e py311-pyqt6
```

### Continuous integration

The GitHub Actions workflow in
[`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs the
test-suite for every combination of Python 3.11 - 3.14 and the PyQt5, PyQt6
and PySide6 bindings. Qt runs headless via `QT_QPA_PLATFORM=offscreen`.

Results are visualised in several places:

* a **test-results table** (tests, passed, failed, skipped, duration) is
  written to the summary of every job and of the combined `Test report` job,
* failing tests are **annotated inline** in the diff via
  `pytest-github-actions-annotate-failures`,
* the raw **JUnit XML** files are uploaded as artifacts and can be downloaded
  from the workflow run,
* the status **badge** at the top of this README shows the latest result.

## Background

`pyqtschema` is inspired by [qt-jsonschema-form](https://github.com/agoose77/qt-jsonschema-form). Due to the author's
lack of [time](https://github.com/agoose77/qt-jsonschema-form/pull/1#issuecomment-595491242) and the missing
[anyOf-support](https://github.com/agoose77/qt-jsonschema-form/blob/ca71ddbf10c2b309c3eb9c4fda6b054a0cb573dd/README.md?plain=1#L10)
, this project was started.
