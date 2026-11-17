"""Colours: a button showing the colour, a click opens the colour dialog.

A string field gets the colour picker with ``"format": "color"`` in the schema
(pydantic: ``json_schema_extra``) or with ``"ui:widget": "color"`` in the
ui-schema (``"colour"`` works as alias).  The state is the colour name ``"#rrggbb"``; a right click on the
button clears it (``None``).  Constraints of the schema (e.g. ``pattern``)
still apply - an invalid value is marked red.
"""
import json
import sys
from typing import Dict, List, NamedTuple, Optional, Type

from pydantic import BaseModel, Field
from qtpy.QtWidgets import QApplication, QGridLayout, QGroupBox, QLabel, QScrollArea, QVBoxLayout, QWidget

from pyqtschema import SchemaWidget

HEX_COLOUR = r"^#[0-9a-fA-F]{6}$"


class Scenario(NamedTuple):
    title: str
    description: str
    model: Type[BaseModel]
    data: Optional[Dict] = None
    ui_schema: Optional[Dict] = None


class SchemaFormat(BaseModel):
    background: str = Field("#ffffff", json_schema_extra={"format": "color"})
    foreground: str = Field("#d32f2f", json_schema_extra={"format": "color"})


class Plain(BaseModel):
    highlight: str = "#2e7d32"
    label: str = "a plain text field for comparison"


class Nullable(BaseModel):
    border: Optional[str] = Field(None, json_schema_extra={"format": "color"})
    shadow: Optional[str] = Field("#9e9e9e", json_schema_extra={"format": "color"})


class Validated(BaseModel):
    accent: str = Field("#1565c0", pattern=HEX_COLOUR, json_schema_extra={"format": "color"})


SCENARIOS: List[Scenario] = [
    Scenario("format: color",
             "the schema selects the colour picker: click the button to choose a colour, "
             "right click to clear it",
             SchemaFormat),
    Scenario("ui:widget: color",
             "a plain str field shown as colour picker by the ui-schema",
             Plain, ui_schema={"highlight": {"ui:widget": "color"}}),
    Scenario("Optional colour",
             "Optional[str]: the checkbox in front switches between None and a colour",
             Nullable),
    Scenario("Validated by the schema",
             f"pattern={HEX_COLOUR}: the colour dialog always returns #rrggbb, but a value from data "
             "like \"blue\" violates the pattern and is marked red",
             Validated, data={"accent": "blue"}),
]


def create_scenario(scenario: Scenario) -> QGroupBox:
    box = QGroupBox(scenario.title)
    layout = QGridLayout(box)

    description = QLabel(scenario.description)
    description.setWordWrap(True)
    lines = [f"data = {json.dumps(scenario.data)}" if scenario.data else "",
             f"ui_schema = {json.dumps(scenario.ui_schema)}" if scenario.ui_schema else ""]
    data = QLabel("\n".join(line for line in lines if line))
    form = SchemaWidget(scenario.model.model_json_schema(), scenario.data, ui_schema=scenario.ui_schema)
    state = QLabel()
    state.setWordWrap(True)

    def show_state(value):
        state.setText(f"state = {json.dumps(value)}  -  valid: {form.is_valid()}")

    form.on_changed.connect(show_state)
    show_state(form.state)

    layout.addWidget(description, 0, 0)
    layout.addWidget(data, 1, 0)
    layout.addWidget(form, 2, 0)
    layout.addWidget(state, 3, 0)
    return box


def create_widget() -> QWidget:
    content = QWidget()
    layout = QVBoxLayout(content)
    for scenario in SCENARIOS:
        layout.addWidget(create_scenario(scenario))

    scroll = QScrollArea()
    scroll.setWindowTitle("pyqtschema - colours")
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    scroll.resize(700, 900)
    return scroll


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = create_widget()
    widget.show()
    app.exec_()
