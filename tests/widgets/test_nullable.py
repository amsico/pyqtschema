"""Nullable fields (``Optional``/``X | None``): a checkbox for ``None``."""
from enum import Enum
from typing import Any, List, Literal, Optional, Union

import pytest
from qtpy.QtWidgets import QVBoxLayout

from pyqtschema import CustomObjectWidget, SchemaWidget
from qtpy.QtCore import Qt

from pyqtschema.widgets import (AnyOfSchemaWidget, EnumSchemaWidget, NullableCheckboxSchemaWidget,
                                NullableSchemaWidget, ObjectSchemaWidget, SpinSchemaWidget, TextSchemaWidget)

pydantic = pytest.importorskip("pydantic")
from pydantic import BaseModel, Field  # noqa: E402

from pyqtschema.pydantic_support import ModelWidgetRegistry, build_widget, to_model  # noqa: E402


class Unit(BaseModel):
    value: float = 1.0
    unit: str = "m"


class Color(Enum):
    red = "red"
    blue = "blue"


class Model(BaseModel):
    my_int: Optional[int] = Field(default=None)
    my_int_5: Optional[int] = 5
    my_str: Optional[str] = None
    my_list: Optional[List[Any]] = None
    my_unit: Optional[Unit] = None
    my_bool: Optional[bool] = None
    my_literal: Optional[Literal["a", "b"]] = None
    my_enum: Optional[Color] = None
    my_union: Union[int, str, None] = None
    my_positive: Optional[int] = Field(None, ge=0)


def make(qtbot, model=Model, data=None, **kwargs) -> SchemaWidget:
    widget = build_widget(model, data, **kwargs)
    qtbot.addWidget(widget)
    return widget


def field(widget: SchemaWidget, name: str) -> NullableSchemaWidget:
    nullable = widget.widget.widgets[name]
    assert isinstance(nullable, NullableSchemaWidget)
    return nullable


@pytest.mark.parametrize("name, inner_cls", [
    ("my_int", SpinSchemaWidget),
    ("my_str", TextSchemaWidget),
    ("my_unit", ObjectSchemaWidget),
    ("my_literal", EnumSchemaWidget),
    ("my_enum", EnumSchemaWidget),
    ("my_union", AnyOfSchemaWidget),
    ("my_positive", SpinSchemaWidget),
])
def test_inner_widget(name, inner_cls, qtbot):
    assert isinstance(field(make(qtbot), name).inner, inner_cls)


def test_default_none_is_kept(qtbot):
    """the reported bug: `int | None = None` became 0 (also in `to_model`)."""
    widget = make(qtbot)
    nullable = field(widget, "my_int")
    assert widget.state["my_int"] is None
    assert not nullable.check.isChecked()
    assert not nullable.inner.isEnabled()
    assert to_model(widget).my_int is None
    assert widget.is_valid()


def test_default_value_is_checked(qtbot):
    widget = make(qtbot)
    assert widget.state["my_int_5"] == 5
    assert field(widget, "my_int_5").check.isChecked()


def test_check_and_uncheck(qtbot):
    widget = make(qtbot)
    nullable = field(widget, "my_int")
    with qtbot.waitSignal(widget.on_changed) as blocker:
        nullable.check.setChecked(True)
    assert blocker.args[0]["my_int"] == 0
    assert nullable.inner.isEnabled()
    nullable.inner.setValue(7)
    assert widget.state["my_int"] == 7
    with qtbot.waitSignal(widget.on_changed) as blocker:
        nullable.check.setChecked(False)
    assert blocker.args[0]["my_int"] is None


def test_data(qtbot):
    widget = make(qtbot, data={"my_int": 3, "my_int_5": None, "my_unit": {"value": 2.0}})
    assert widget.state["my_int"] == 3
    assert widget.state["my_int_5"] is None
    assert widget.state["my_unit"] == {"value": 2.0, "unit": "m"}
    widget.state = {"my_int": None}
    assert widget.state["my_int"] is None


def test_model_instance_roundtrip(qtbot):
    instance = Model(my_int=1, my_str="", my_list=[], my_unit=Unit(value=3))
    widget = make(qtbot, instance)
    assert to_model(widget) == instance


def test_empty_string_is_not_none(qtbot):
    """"" and None stay distinguishable."""
    widget = make(qtbot, data={"my_str": ""})
    assert widget.state["my_str"] == ""
    widget.state = {"my_str": None}
    assert widget.state["my_str"] is None


def test_empty_list_is_not_none(qtbot):
    widget = make(qtbot)
    assert widget.state["my_list"] is None
    widget.state = {"my_list": []}
    assert widget.state["my_list"] == []


def test_required_nullable_without_default(qtbot):
    class Required(BaseModel):
        value: Optional[int]

    widget = make(qtbot, Required)
    assert widget.state == {"value": None}
    assert widget.is_valid()
    assert to_model(widget).value is None


def test_errors_are_specific_and_routed(qtbot):
    """`int | None` with `ge=0`: the error names the violated bound, the inner widget is marked."""
    widget = make(qtbot, data={"my_positive": 1})
    nullable = field(widget, "my_positive")
    nullable.inner.setMinimum(-10)  # allow an invalid value to test the validation
    nullable.inner.setValue(-1)
    errors = widget.errors()
    assert len(errors) == 1
    assert "minimum" in errors[0].message
    widget.show_errors()
    assert nullable.inner.toolTip() == errors[0].message


def test_read_only(qtbot):
    widget = make(qtbot, data={"my_int_5": 5})
    unchecked, checked = field(widget, "my_int"), field(widget, "my_int_5")
    widget.set_read_only(True)
    assert not unchecked.check.isEnabled() and not checked.check.isEnabled()
    assert not checked.inner.isEnabled()
    widget.set_read_only(False)
    assert unchecked.check.isEnabled()
    assert not unchecked.inner.isEnabled()  # still None: stays disabled
    assert checked.inner.isEnabled()


def test_ui_options_reach_inner_widget(qtbot):
    widget = make(qtbot, ui_schema={"my_int": {"ui:step": 10}})
    assert field(widget, "my_int").inner.singleStep() == 10


def test_registry_applies_to_inner_widget(qtbot):
    class UnitWidget(CustomObjectWidget):
        def setup_ui(self):
            QVBoxLayout(self).addWidget(self.build_field("value"))

    registry = ModelWidgetRegistry()
    registry.register_model(Unit, UnitWidget)
    widget = make(qtbot, data={"my_unit": {"value": 4.0}}, registry=registry)
    nullable = field(widget, "my_unit")
    assert isinstance(nullable.inner, UnitWidget)
    assert widget.state["my_unit"] == {"value": 4.0, "unit": "m"}


def test_without_normalize_any_of_is_kept(qtbot):
    widget = make(qtbot, normalize=False)
    assert isinstance(widget.widget.widgets["my_int"], AnyOfSchemaWidget)


def test_type_list_schema(qtbot):
    schema = {"type": "object", "properties": {"x": {"type": ["integer", "null"], "default": 5}}}
    widget = SchemaWidget(schema, data={"x": None})
    qtbot.addWidget(widget)
    assert widget.state == {"x": None}
    widget.state = {"x": 3}
    assert widget.state == {"x": 3}



def test_optional_bool_is_one_tristate_checkbox(qtbot):
    """`Optional[bool]`: one tristate checkbox (partially checked: None), titled like a bool."""
    widget = make(qtbot)
    box = widget.widget.widgets["my_bool"]
    assert isinstance(box, NullableCheckboxSchemaWidget)
    assert box.isTristate()
    assert box.text() == "My Bool (None)"
    assert box.checkState() == Qt.PartiallyChecked
    assert widget.state["my_bool"] is None
    assert widget.is_valid()


@pytest.mark.parametrize("value, check_state", [
    (True, Qt.Checked), (False, Qt.Unchecked), (None, Qt.PartiallyChecked)])
def test_optional_bool_state(value, check_state, qtbot):
    widget = make(qtbot, data={"my_bool": not value if value is not None else True})
    box = widget.widget.widgets["my_bool"]
    widget.state = {"my_bool": value}
    assert box.checkState() == check_state
    assert widget.state["my_bool"] is value
    assert to_model(widget).my_bool is value


def test_optional_bool_click_cycles(qtbot):
    widget = make(qtbot)
    box = widget.widget.widgets["my_bool"]
    seen = []
    for _ in range(3):
        with qtbot.waitSignal(widget.on_changed):
            box.click()
        seen.append(widget.state["my_bool"])
    assert seen == [True, False, None]


def test_optional_bool_default(qtbot):
    class WithDefault(BaseModel):
        flag: Optional[bool] = False

    widget = make(qtbot, WithDefault)
    assert widget.state == {"flag": False}


def test_optional_bool_with_ui_widget_keeps_wrapper(qtbot):
    """an explicit ui:widget is honored: the generic wrapper is used."""
    widget = make(qtbot, ui_schema={"my_bool": {"ui:widget": "checkbox"}})
    assert isinstance(widget.widget.widgets["my_bool"], NullableSchemaWidget)



def test_optional_bool_none_suffix_follows_state(qtbot):
    widget = make(qtbot)
    box = widget.widget.widgets["my_bool"]
    widget.state = {"my_bool": True}
    assert box.text() == "My Bool"
    widget.state = {"my_bool": False}
    assert box.text() == "My Bool"
    widget.state = {"my_bool": None}
    assert box.text() == "My Bool (None)"


def test_optional_bool_none_suffix_hidden_by_ui_option(qtbot):
    widget = make(qtbot, ui_schema={"my_bool": {"ui:show_none": False}})
    box = widget.widget.widgets["my_bool"]
    assert isinstance(box, NullableCheckboxSchemaWidget)
    assert widget.state["my_bool"] is None
    assert box.text() == "My Bool"
