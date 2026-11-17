"""Numeric fields: bounds, steps and decimals - every scenario side by side.

Each scenario shows a pydantic model and a ui-schema next to the rendered
form and its current state.  Schema-keywords (``ge``, ``gt``, ``multiple_of``,
...) are data rules and validated; ``ui:*``-options only change the
presentation.  Details: the docstring of ``pyqtschema.widgets.numeric``.

Conflicts between ui-schema and schema are logged as warnings (the schema
wins) - they are printed to the console.
"""
import json
import logging
import sys
from typing import Dict, List, NamedTuple, Optional, Type

from pydantic import BaseModel, Field
from qtpy.QtWidgets import (QApplication, QGridLayout, QGroupBox, QLabel, QScrollArea, QVBoxLayout, QWidget)

from pyqtschema import SchemaWidget


class Scenario(NamedTuple):
    title: str
    description: str
    model: Type[BaseModel]
    ui_schema: Optional[Dict] = None


# --- schema: bounds --------------------------------------------------------

class Unbounded(BaseModel):
    count: int = -5
    value: float = -1e12


class Inclusive(BaseModel):
    count: int = Field(3, ge=2, le=10)
    value: float = Field(0.5, ge=0, le=1)


class Exclusive(BaseModel):
    count: int = Field(5, gt=2, lt=10)
    value: float = Field(1.0, gt=0)


class Large(BaseModel):
    count: int = Field(0, ge=-10 ** 12, le=10 ** 12)


# --- schema: steps ---------------------------------------------------------

class MultipleOf(BaseModel):
    count: int = Field(10, ge=0, le=100, multiple_of=5)
    value: float = Field(0.5, ge=0, le=10, multiple_of=0.25)


# --- ui-schema -------------------------------------------------------------

class Plain(BaseModel):
    count: int = 0
    value: float = 0.0


class Ratio(BaseModel):
    ratio: float = Field(0.5, ge=0, le=1)


class Percent(BaseModel):
    percent: int = Field(50, ge=0, le=100)


class Fine(BaseModel):
    value: float = Field(0.125, multiple_of=0.001)


SCENARIOS: List[Scenario] = [
    Scenario("Unbounded",
             "no bounds: negative values are allowed; integer -2**31 .. 2**31-1, number -inf .. inf",
             Unbounded),
    Scenario("Inclusive bounds (ge / le)",
             "count: ge=2, le=10 / value: ge=0, le=1",
             Inclusive),
    Scenario("Exclusive bounds (gt / lt)",
             "count: gt=2, lt=10 -> 3 .. 9 / value: gt=0 -> 0.01 (smallest displayable step)",
             Exclusive),
    Scenario("Beyond 32 bit",
             "ge=-10**12, le=10**12: clamped to the 32-bit range of the spin box (warning)",
             Large),
    Scenario("Step from the schema (multiple_of)",
             "count: multiple_of=5 / value: multiple_of=0.25 - step AND validation rule",
             MultipleOf),
    Scenario("ui:min / ui:max",
             "bounds for fields without schema-bounds - presentation only, not validated",
             Plain, {"count": {"ui:min": -10, "ui:max": 10}, "value": {"ui:min": 0, "ui:max": 5}}),
    Scenario("ui:min / ui:max conflicting with the schema",
             "ge=2, le=10 vs. ui:min=0, ui:max=50: the schema wins (warning)",
             Inclusive, {"count": {"ui:min": 0, "ui:max": 50}}),
    Scenario("ui:step",
             "count: steps of 10 / ratio: steps of 0.05 - without a validation rule",
             Plain, {"count": {"ui:step": 10}, "value": {"ui:step": 0.05}}),
    Scenario("ui:step conflicting with multiple_of",
             "multiple_of=5 vs. ui:step=3: not a multiple -> multiple_of is used (warning); "
             "multiple_of=0.25 vs. ui:step=1: a multiple -> ui:step is used",
             MultipleOf, {"count": {"ui:step": 3}, "value": {"ui:step": 1}}),
    Scenario("ui:decimals",
             "ratio: 3 decimals, steps of 0.005",
             Ratio, {"ratio": {"ui:decimals": 3, "ui:step": 0.005}}),
    Scenario("ui:decimals conflicting with the schema",
             "multiple_of=0.001 needs 3 decimals vs. ui:decimals=1: raised to 3 (warning)",
             Fine, {"value": {"ui:decimals": 1}}),
    Scenario("Slider (ui:widget: range)",
             "needs both bounds: from the schema (ge=0, le=100) and ui:step=10 for the ticks",
             Percent, {"percent": {"ui:widget": "range", "ui:step": 10}}),
]


def create_scenario(scenario: Scenario) -> QGroupBox:
    box = QGroupBox(scenario.title)
    layout = QGridLayout(box)

    description = QLabel(scenario.description)
    description.setWordWrap(True)
    ui_schema = QLabel(f"ui_schema = {json.dumps(scenario.ui_schema)}" if scenario.ui_schema else "")
    form = SchemaWidget(scenario.model.model_json_schema(), ui_schema=scenario.ui_schema)
    state = QLabel()

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
    scroll.setWindowTitle("pyqtschema - numeric fields")
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    scroll.resize(700, 900)
    return scroll


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    app = QApplication(sys.argv)
    widget = create_widget()
    widget.show()
    app.exec_()
