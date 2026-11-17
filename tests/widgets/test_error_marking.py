"""Fields with a validation error are marked with a red border (style sheet, not palette)."""
from qtpy.QtWidgets import QApplication

from pyqtschema import SchemaWidget


class Error:
    message = "something is wrong"


def make(qtbot, schema, data=None) -> SchemaWidget:
    widget = SchemaWidget(schema, data, validate=False)
    qtbot.addWidget(widget)
    return widget


SCHEMA = {"type": "object", "properties": {
    "text": {"type": "string", "minLength": 3},
    "count": {"type": "integer", "minimum": 0},
    "color": {"type": "string", "format": "colour", "default": "#00ff00"},
}}


def test_show_errors_marks_the_fields(qtbot):
    widget = make(qtbot, SCHEMA, {"text": "a"})
    text, count = widget.widget.widgets["text"], widget.widget.widgets["count"]
    widget.show_errors()
    assert text.is_marked_invalid()
    assert "border" in text.styleSheet()
    assert text.toolTip() == "'a' is too short"
    assert not count.is_marked_invalid()
    assert count.styleSheet() == ""


def test_change_clears_the_mark(qtbot):
    widget = make(qtbot, SCHEMA, {"text": "a"})
    text = widget.widget.widgets["text"]
    widget.show_errors()
    text.setText("abc")
    assert not text.is_marked_invalid()
    assert text.styleSheet() == ""
    assert text.toolTip() == ""


def test_own_style_sheet_is_kept(qtbot):
    """the colour button's own style sheet survives marking and unmarking."""
    widget = make(qtbot, SCHEMA)
    color = widget.widget.widgets["color"]
    own = color.styleSheet()
    assert "#00ff00" in own
    color.handle_error((), Error())
    assert color.is_marked_invalid()
    assert color.styleSheet().startswith(own)
    color.clear_error()
    assert color.styleSheet() == own


def test_mark_does_not_apply_to_children(qtbot):
    """an object marked as a whole: only the group box gets the border, not its fields."""
    schema = {"type": "object", "properties": {"inner": {"type": "object", "properties": {"v": {"type": "integer"}}}}}
    widget = make(qtbot, schema)
    inner = widget.widget.widgets["inner"]
    inner._set_valid_state(Error())
    QApplication.processEvents()
    assert inner.is_marked_invalid()
    assert not inner.widgets["v"].property("schemaInvalid")
