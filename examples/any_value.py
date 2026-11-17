"""Values of any type (``Any``, ``Dict[str, Any]``) edited as JSON.

Fields the schema does not restrict to a type are shown as a JSON text field:
``42``, ``"text"``, ``[1, 2]``, ``{"key": 1}``, ``null`` (or empty).  The input
is parsed strictly: invalid JSON is marked red (tooltip: the parse error) and
the state keeps the last valid value - ``hello`` is not taken as ``"hello"``.
Any field can be edited as JSON with ``"ui:widget": "json"``.
"""
import json
import sys
from typing import Any, Dict, List, NamedTuple, Optional, Type

from pydantic import BaseModel
from qtpy.QtWidgets import QApplication, QGridLayout, QGroupBox, QLabel, QScrollArea, QVBoxLayout, QWidget

from pyqtschema import SchemaWidget


class Scenario(NamedTuple):
    title: str
    description: str
    model: Type[BaseModel]
    ui_schema: Optional[Dict] = None


class AnyValues(BaseModel):
    anything: Any = None
    number_or_text: Any = 42
    optional_any: Optional[Any] = None


class Collections(BaseModel):
    items: List[Any] = [1, "x", {"nested": True}]
    mapping: Dict[str, Any] = {"key": 1, "list": [1, 2]}


class Typed(BaseModel):
    count: int = 1
    tags: List[str] = ["a", "b"]


SCENARIOS: List[Scenario] = [
    Scenario("Any",
             "type a JSON value; invalid JSON (e.g. hello without quotes) is marked and not taken over. "
             "Optional[Any] needs no checkbox: null is a JSON value",
             AnyValues),
    Scenario("List[Any] and Dict[str, Any]",
             "every list item is a JSON field; a dict without fixed keys is one JSON field",
             Collections),
    Scenario("ui:widget: json",
             "typed fields edited as JSON - the schema still validates the type",
             Typed, {"count": {"ui:widget": "json"}, "tags": {"ui:widget": "json"}}),
]


def create_scenario(scenario: Scenario) -> QGroupBox:
    box = QGroupBox(scenario.title)
    layout = QGridLayout(box)

    description = QLabel(scenario.description)
    description.setWordWrap(True)
    ui_schema = QLabel(f"ui_schema = {json.dumps(scenario.ui_schema)}" if scenario.ui_schema else "")
    form = SchemaWidget(scenario.model.model_json_schema(), ui_schema=scenario.ui_schema)
    state = QLabel()
    state.setWordWrap(True)

    def show_state(value):
        state.setText(f"state = {json.dumps(value)}  -  valid: {form.is_valid()}")

    form.on_changed.connect(show_state)
    show_state(form.state)

    layout.addWidget(description, 0, 0)
    layout.addWidget(ui_schema, 1, 0)
    layout.addWidget(form, 2, 0)
    layout.addWidget(state, 3, 0)
    return box


def create_widget() -> QWidget:
    content = QWidget()
    layout = QVBoxLayout(content)
    for scenario in SCENARIOS:
        layout.addWidget(create_scenario(scenario))

    scroll = QScrollArea()
    scroll.setWindowTitle("pyqtschema - values of any type")
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    scroll.resize(700, 900)
    return scroll


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = create_widget()
    widget.show()
    app.exec_()
