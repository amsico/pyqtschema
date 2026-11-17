"""Tests for :class:`SchemaWidget`, custom widgets and read-only handling."""
import pytest
from qtpy.QtWidgets import QLabel, QLineEdit, QVBoxLayout

from pyqtschema import CustomObjectWidget, SchemaWidget, WidgetRegistry
from pyqtschema.widgets import ObjectSchemaWidget, TextSchemaWidget

SCHEMA = {
    "title": "Limits",
    "type": "object",
    "properties": {
        "name": {"title": "Name", "type": "string", "default": "dummy"},
        "upper": {"$ref": "#/$defs/Unit", "title": "Upper"},
        "lower": {"anyOf": [{"$ref": "#/$defs/Unit"}, {"type": "null"}], "title": "Lower"},
    },
    "$defs": {
        "Unit": {
            "title": "Unit",
            "type": "object",
            "properties": {
                "value": {"title": "Value", "type": "number", "default": 1.0},
                "unit": {"title": "Unit", "type": "string", "default": "m"},
            },
            "required": ["value"],
        },
    },
}


class UnitWidget(CustomObjectWidget):
    """Custom widget showing only the value (unit stays in the state)."""

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.property_title("value"), self))
        layout.addWidget(self.build_field("value"))


def make(qtbot, *args, **kwargs) -> SchemaWidget:
    widget = SchemaWidget(*args, **kwargs)
    qtbot.addWidget(widget)
    return widget


def test_defaults_without_data(qtbot):
    widget = make(qtbot, SCHEMA)
    assert widget.state["name"] == "dummy"
    assert widget.state["upper"] == {"value": 1.0, "unit": "m"}
    assert isinstance(widget.widget.widgets["upper"], ObjectSchemaWidget)


def test_partial_data_keeps_defaults_and_ignores_unknown(qtbot):
    widget = make(qtbot, SCHEMA, {"upper": {"value": 5}, "unknown": 1})
    assert widget.state["name"] == "dummy"
    assert widget.state["upper"] == {"value": 5.0, "unit": "m"}
    assert "unknown" not in widget.state


def test_ref_siblings_are_merged(qtbot):
    widget = make(qtbot, SCHEMA)
    assert widget.widget.widgets["upper"].title() == "Upper"


def test_nullable_ref_is_built(qtbot):
    widget = make(qtbot, SCHEMA)
    assert isinstance(widget.widget.widgets["lower"], ObjectSchemaWidget)


def test_on_changed(qtbot):
    widget = make(qtbot, SCHEMA)
    with qtbot.waitSignal(widget.on_changed) as blocker:
        widget.widget.widgets["name"].setText("changed")
    assert blocker.args[0]["name"] == "changed"


def test_validation(qtbot):
    widget = make(qtbot, {"type": "object", "properties": {"n": {"type": "string", "minLength": 3}}},
                  {"n": "abcd"})
    assert widget.is_valid()
    widget.state = {"n": "a"}
    assert not widget.is_valid()
    assert not widget.show_errors()
    assert not widget.form.error_widget.isHidden()


@pytest.mark.parametrize("key, registration", [
    ("ref", lambda r: r.register("unit", UnitWidget, ref="Unit")),
    # a list registers several paths (a tuple is *one* path: ("a", "b") == "a.b")
    ("path", lambda r: r.register("unit", UnitWidget, path=["upper", "lower"])),
])
def test_custom_widget_by_ref_or_path(qtbot, key, registration):
    registry = WidgetRegistry()
    registration(registry)
    widget = make(qtbot, SCHEMA, {"upper": {"value": 3, "unit": "km"}}, registry=registry)
    upper = widget.widget.widgets["upper"]
    assert isinstance(upper, UnitWidget)
    assert isinstance(widget.widget.widgets["lower"], UnitWidget)
    # not-built properties are passed through unchanged
    assert widget.state["upper"] == {"value": 3.0, "unit": "km"}

    with qtbot.waitSignal(widget.on_changed) as blocker:
        upper.widgets["value"].setValue(7)
    assert blocker.args[0]["upper"] == {"value": 7.0, "unit": "km"}


def test_custom_widget_by_schema_marker(qtbot):
    registry = WidgetRegistry()
    registry.register("unit", UnitWidget)
    schema = {"type": "object", "properties": {"u": {"type": "object", "x-widget": "unit",
                                                     "properties": {"value": {"type": "number"}}}}}
    widget = make(qtbot, schema, registry=registry)
    assert isinstance(widget.widget.widgets["u"], UnitWidget)


def test_custom_widget_error_routing(qtbot):
    class CodeWidget(CustomObjectWidget):
        def setup_ui(self):
            QVBoxLayout(self).addWidget(self.build_field("code"))

    schema = {"type": "object", "properties": {"item": {"$ref": "#/$defs/Item"}},
              "$defs": {"Item": {"type": "object", "properties": {
                  "code": {"type": "string", "minLength": 2, "default": "ab"}}}}}
    registry = WidgetRegistry()
    registry.register("item", CodeWidget, ref="Item")
    widget = make(qtbot, schema, registry=registry)
    widget.state = {"item": {"code": "x"}}
    errors = widget.errors()
    assert [list(err.path) for err in errors] == [["item", "code"]]
    widget.widget.handle_error(tuple(errors[0].path), errors[0])
    assert widget.widget.widgets["item"].widgets["code"].toolTip() == errors[0].message


def test_child_registry_overrides(qtbot):
    class OtherWidget(UnitWidget):
        pass

    registry = WidgetRegistry()
    registry.register("unit", UnitWidget, ref="Unit")
    child = registry.child()
    child.register("other", OtherWidget, path="upper")
    widget = make(qtbot, SCHEMA, registry=child)
    assert type(widget.widget.widgets["upper"]) is OtherWidget
    assert type(widget.widget.widgets["lower"]) is UnitWidget


def test_translator_and_rebuild(qtbot):
    widget = make(qtbot, SCHEMA, {"name": "kept"}, translator=str.upper)
    assert widget.schema["properties"]["name"]["title"] == "NAME"
    widget.set_translator(str.lower)
    assert widget.schema["properties"]["name"]["title"] == "name"
    assert widget.state["name"] == "kept"


def test_read_only(qtbot):
    widget = make(qtbot, SCHEMA, ui_schema={"lower": {"unit": {"ui:disabled": True}}})
    edits = widget.findChildren(QLineEdit)
    assert edits
    widget.set_read_only(True)
    assert widget.is_read_only()
    assert not any(edit.isEnabled() for edit in edits)
    widget.set_read_only(False)
    name = widget.widget.widgets["name"]
    assert isinstance(name, TextSchemaWidget) and name.isEnabled()
    assert not widget.widget.widgets["lower"].widgets["unit"].isEnabled()  # ui:disabled stays


def test_read_only_delegates_to_custom_widget(qtbot):
    calls = []

    class ReadOnlyUnit(UnitWidget):
        def set_read_only(self, read_only):
            calls.append(read_only)

    registry = WidgetRegistry()
    registry.register("unit", ReadOnlyUnit, ref="Unit")
    widget = make(qtbot, SCHEMA, registry=registry)
    widget.set_read_only(True)
    assert calls == [True, True]  # upper + lower
