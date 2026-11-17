"""The colour picker (``"format": "color"``, alias ``"colour"``)."""
import pytest

from pyqtschema import SchemaWidget
from pyqtschema.widgets import ColorSchemaWidget, TextSchemaWidget


def make(qtbot, schema, ui_schema=None) -> SchemaWidget:
    widget = SchemaWidget({"type": "object", "properties": {"c": schema}}, ui_schema=ui_schema)
    qtbot.addWidget(widget)
    return widget


@pytest.mark.parametrize("name", ["color", "colour"])
def test_format_selects_the_colour_picker(name, qtbot):
    widget = make(qtbot, {"type": "string", "format": name, "default": "#ff0000"})
    assert isinstance(widget.widget.widgets["c"], ColorSchemaWidget)
    assert widget.state == {"c": "#ff0000"}


@pytest.mark.parametrize("name", ["color", "colour"])
def test_ui_widget_selects_the_colour_picker(name, qtbot):
    widget = make(qtbot, {"type": "string"}, ui_schema={"c": {"ui:widget": name}})
    assert isinstance(widget.widget.widgets["c"], ColorSchemaWidget)


def test_without_format_a_text_field(qtbot):
    assert isinstance(make(qtbot, {"type": "string"}).widget.widgets["c"], TextSchemaWidget)


def test_set_colour_emits_the_state(qtbot):
    widget = make(qtbot, {"type": "string", "format": "color"})
    with qtbot.waitSignal(widget.on_changed):
        widget.widget.widgets["c"].setColor("#00ff00")
    assert widget.state == {"c": "#00ff00"}


@pytest.mark.parametrize("schema", [
    {"type": "string", "default": "#ff0000", "pattern": "^#[0-9a-f]{6}$"},
    {"type": ["string", "null"], "default": None},
    {"anyOf": [{"type": "string"}, {"type": "null"}], "default": "#00ff00"},
], ids=["plain", "nullable", "optional"])
def test_alias_colour_behaves_like_color(schema, qtbot):
    """`"colour"` is only another name: same widget, state and validation as `"color"`."""
    color, colour = (make(qtbot, {**schema, "format": name}) for name in ("color", "colour"))
    widget_color, widget_colour = color.widget.widgets["c"], colour.widget.widgets["c"]
    assert type(widget_color) is type(widget_colour)
    inner = getattr(widget_colour, "inner", widget_colour)
    assert isinstance(inner, ColorSchemaWidget)
    assert colour.state == color.state

    for form in (color, colour):
        target = getattr(form.widget.widgets["c"], "inner", form.widget.widgets["c"])
        if hasattr(form.widget.widgets["c"], "check"):
            form.widget.widgets["c"].check.setChecked(True)
        target.setColor("#0000ff")
    assert colour.state == color.state == {"c": "#0000ff"}
    assert colour.is_valid() == color.is_valid()
