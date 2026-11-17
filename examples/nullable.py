"""Nullable fields (``X | None``): a checkbox for ``None`` in front of the field.

Unchecked, the field is ``None`` and its widget is disabled; checked, the field
has the value of its widget.  ``""``/``[]`` and ``None`` stay distinguishable.
Every type works the same way - numbers, text, lists, enums, nested models.
Details: the docstring of ``pyqtschema.widgets.nullable``.
"""
import json
import sys
from enum import Enum
from typing import Any, Dict, List, Literal, NamedTuple, Optional, Type, Union

from pydantic import BaseModel, Field
from qtpy.QtWidgets import QApplication, QGridLayout, QGroupBox, QLabel, QScrollArea, QVBoxLayout, QWidget

from pyqtschema import SchemaWidget


class Scenario(NamedTuple):
    title: str
    description: str
    model: Type[BaseModel]
    data: Optional[Dict] = None
    normalize: bool = True
    ui_schema: Optional[Dict] = None


class Numbers(BaseModel):
    my_int: Optional[int] = Field(default=None)
    my_int_5: Optional[int] = 5
    my_positive: Optional[int] = Field(None, ge=0, description="ge=0 applies to the value")


class Texts(BaseModel):
    my_string: Optional[str] = None
    my_list: Optional[List[str]] = None
    my_list_any: Optional[List[Any]] = None


class Color(Enum):
    red = "red"
    blue = "blue"


class Choices(BaseModel):
    my_plain_bool: bool = False
    my_bool: Optional[bool] = None
    my_literal: Optional[Literal["a", "b"]] = None
    my_enum: Optional[Color] = None
    my_union: Union[int, str, None] = None


class Unit(BaseModel):
    value: float = 1.0
    unit: str = "m"


class Limits(BaseModel):
    upper: Unit = Unit()
    lower: Optional[Unit] = None


class Required(BaseModel):
    value: Optional[int]


SCENARIOS: List[Scenario] = [
    Scenario("Numbers",
             "default None -> unchecked (None); default 5 -> checked; constraints apply to the value",
             Numbers),
    Scenario("Text and lists",
             "unchecked: None, checked and empty: \"\" / [] - both stay distinguishable",
             Texts, {"my_string": ""}),
    Scenario("Choices",
             "bool: a plain checkbox (True/False) for comparison; Optional[bool]: one tristate checkbox "
             "(partially checked: None, shown as \"(None)\"; a click cycles None -> True -> False); Literal, Enum "
             "and a union of types: the checkbox comes in front of the choice",
             Choices),
    Scenario("Optional[bool] without \"(None)\"",
             "ui:show_none: false hides the \"(None)\" next to the title",
             Choices, ui_schema={"my_bool": {"ui:show_none": False}}),
    Scenario("Nested model",
             "Optional[Unit]: unchecked None, checked the sub-form (custom widgets of the registry apply)",
             Limits),
    Scenario("Required, but nullable",
             "value: Optional[int] without default - required, None is valid",
             Required),
    Scenario("Without normalization",
             "SchemaWidget(..., normalize=False) renders the schema as given: a choice integer / null",
             Numbers, normalize=False),
]


def create_scenario(scenario: Scenario) -> QGroupBox:
    box = QGroupBox(scenario.title)
    layout = QGridLayout(box)

    description = QLabel(scenario.description)
    description.setWordWrap(True)
    lines = [f"data = {json.dumps(scenario.data)}" if scenario.data else "",
             f"ui_schema = {json.dumps(scenario.ui_schema)}" if scenario.ui_schema else ""]
    data = QLabel("\n".join(line for line in lines if line))
    form = SchemaWidget(scenario.model.model_json_schema(), scenario.data, normalize=scenario.normalize,
                        ui_schema=scenario.ui_schema)
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
    scroll.setWindowTitle("pyqtschema - nullable fields")
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    scroll.resize(700, 900)
    return scroll


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = create_widget()
    widget.show()
    app.exec_()
