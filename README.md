# pyqtschema

`pyqtschema` allows the generation of a graphical representation of a [jsonschema](https://json-schema.org/). A given
schema is translated to QWidgets.

## Installation

As usual:
* install the pypi version
  
  `pip install pyqtschema`

* or clone the repository

  `pip install git+https://github.com/amsico/pyqtschema.git`

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
