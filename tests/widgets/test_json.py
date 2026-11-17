"""Values of any type (pydantic `Any`, `Dict[str, Any]`) edited as JSON."""
from typing import Any, Dict, List, Optional

import pytest
from qtpy.QtCore import QPoint, Qt
from qtpy.QtTest import QTest

from pyqtschema import SchemaWidget
from pyqtschema.schema import normalize_schema
from pyqtschema.widgets import ArraySchemaWidget, JsonSchemaWidget, SpinSchemaWidget

pydantic = pytest.importorskip("pydantic")
from pydantic import BaseModel  # noqa: E402

from pyqtschema.pydantic_support import build_widget, to_model  # noqa: E402


class Model(BaseModel):
    anything: Any = None
    items: List[Any] = [1, "x"]
    mapping: Dict[str, Any] = {"k": 1}
    required_mapping: Dict[str, Any]
    optional_any: Optional[Any] = 3


def make(qtbot, model=Model, data=None, **kwargs) -> SchemaWidget:
    widget = build_widget(model, data, **kwargs)
    qtbot.addWidget(widget)
    return widget


def edit(widget: JsonSchemaWidget, text: str) -> None:
    """change the text like a user."""
    widget.setPlainText(text)


@pytest.mark.parametrize("name", ["anything", "mapping", "required_mapping", "optional_any"])
def test_json_widget_is_used(name, qtbot):
    assert isinstance(make(qtbot).widget.widgets[name], JsonSchemaWidget)


def test_defaults_and_text(qtbot):
    widget = make(qtbot)
    assert widget.state == {"anything": None, "items": [1, "x"], "mapping": {"k": 1}, "required_mapping": {},
                            "optional_any": 3}
    assert widget.widget.widgets["anything"].toPlainText() == ""
    assert widget.widget.widgets["mapping"].toPlainText() == '{\n  "k": 1\n}'
    assert widget.is_valid()


@pytest.mark.parametrize("text, value", [
    ("2", 2), ('"2"', "2"), ("[1,2]", [1, 2]), ('[1, "2"]', [1, "2"]), ('{"as":2}', {"as": 2}),
    ("42", 42), ('"hello"', "hello"), ('{"a": {"b": null}}', {"a": {"b": None}}),
    ("true", True), ("null", None), ("", None), ("  ", None)])
def test_valid_json(text, value, qtbot):
    widget = make(qtbot)
    json_widget = widget.widget.widgets["anything"]
    edit(json_widget, text)
    assert widget.state["anything"] == value
    assert json_widget.is_valid_json()
    assert json_widget.toolTip() == ""


@pytest.mark.parametrize("text", ['{"as"}', "hello", "[1, 2", "{'a': 1}", "1a"])
def test_invalid_json_is_strict(text, qtbot):
    """invalid JSON is marked and not reinterpreted: the state keeps the last valid value."""
    widget = make(qtbot, data={"anything": [1]})
    json_widget = widget.widget.widgets["anything"]
    edit(json_widget, text)
    assert widget.state["anything"] == [1]
    assert not json_widget.is_valid_json()
    assert json_widget.toolTip().startswith("invalid JSON")


def test_invalid_json_does_not_emit(qtbot):
    widget = make(qtbot)
    with qtbot.assertNotEmitted(widget.on_changed):
        edit(widget.widget.widgets["anything"], "[1,")


def test_fixing_invalid_json_clears_the_mark(qtbot):
    widget = make(qtbot)
    json_widget = widget.widget.widgets["anything"]
    edit(json_widget, "[1,")
    with qtbot.waitSignal(widget.on_changed):
        edit(json_widget, "[1, 2]")
    assert widget.state["anything"] == [1, 2]
    assert json_widget.toolTip() == ""


def test_data_and_to_model(qtbot):
    widget = make(qtbot, data={"anything": {"x": [1]}, "required_mapping": {"a": "b"}})
    assert widget.widget.widgets["anything"].toPlainText() == '{\n  "x": [\n    1\n  ]\n}'
    model = to_model(widget)
    assert model.anything == {"x": [1]}
    assert model.required_mapping == {"a": "b"}


def test_list_of_any_items(qtbot):
    widget = make(qtbot)
    array = widget.widget.widgets["items"]
    assert isinstance(array, ArraySchemaWidget)
    assert all(isinstance(row.widget, JsonSchemaWidget) for row in array.rows)
    array.add_item()
    assert widget.state["items"] == [1, "x", None]


def test_optional_any_has_no_null_checkbox():
    """`Optional[Any]` accepts null anyway - no checkbox in front of the JSON field."""
    node = {"anyOf": [{}, {"type": "null"}], "default": 3, "title": "E"}
    assert normalize_schema(node) == {"default": 3, "title": "E"}


def test_ui_widget_json_for_typed_field(qtbot):
    schema = {"type": "object", "properties": {"n": {"type": "integer", "default": 1}}}
    plain = SchemaWidget(schema)
    as_json = SchemaWidget(schema, ui_schema={"n": {"ui:widget": "json"}})
    qtbot.addWidget(plain)
    qtbot.addWidget(as_json)
    assert isinstance(plain.widget.widgets["n"], SpinSchemaWidget)
    assert isinstance(as_json.widget.widgets["n"], JsonSchemaWidget)
    edit(as_json.widget.widgets["n"], '"text"')
    assert not as_json.is_valid()  # the schema still validates the type


def test_empty_schema_property(qtbot):
    """a property without schema (`{}`) crashed the builder (UnboundLocalError)."""
    widget = SchemaWidget({"type": "object", "properties": {"x": {}}})
    qtbot.addWidget(widget)
    assert isinstance(widget.widget.widgets["x"], JsonSchemaWidget)
    assert widget.state == {"x": None}

@pytest.mark.parametrize("value, text", [
    (None, ""), (2, "2"), ("2", '"2"'), ([], "[]"), ({}, "{}"), ([1, "2"], '[\n  1,\n  "2"\n]')])
def test_format(value, text):
    assert JsonSchemaWidget.format(value) == text


def test_multi_line_input(qtbot):
    widget = make(qtbot)
    edit(widget.widget.widgets["anything"], '{\n  "a": 1,\n  "b": [1, 2]\n}')
    assert widget.state["anything"] == {"a": 1, "b": [1, 2]}


def test_parse_error_names_the_line(qtbot):
    widget = make(qtbot)
    json_widget = widget.widget.widgets["anything"]
    edit(json_widget, '{\n  "a": 1\n  "b": 2\n}')
    assert "line 3" in json_widget.toolTip()


def test_height_fits_the_content(qtbot):
    widget = make(qtbot, data={"anything": {f"k{i}": i for i in range(5)}})
    small, large = widget.widget.widgets["optional_any"], widget.widget.widgets["anything"]
    assert small.height() == small._height_for_rows(JsonSchemaWidget.MIN_ROWS)
    assert large.height() == large._height_for_rows(7)  # 5 keys + braces


def test_height_is_capped(qtbot):
    widget = make(qtbot, data={"anything": list(range(50))})
    json_widget = widget.widget.widgets["anything"]
    assert json_widget.height() == json_widget._height_for_rows(JsonSchemaWidget.MAX_ROWS)


def test_grip_resizes_the_height(qtbot):
    widget = make(qtbot)
    widget.show()
    qtbot.waitExposed(widget)
    json_widget = widget.widget.widgets["anything"]
    grip = json_widget.grip
    before = json_widget.height()
    start = QPoint(grip.width() // 2, grip.height() // 2)
    qtbot.mousePress(grip, Qt.LeftButton, pos=start)
    QTest.mouseMove(grip, start + QPoint(0, 60))
    qtbot.mouseRelease(grip, Qt.LeftButton, pos=start + QPoint(0, 60))
    assert json_widget.height() > before
    # not below one row
    qtbot.mousePress(grip, Qt.LeftButton, pos=start)
    QTest.mouseMove(grip, start - QPoint(0, 1000))
    qtbot.mouseRelease(grip, Qt.LeftButton, pos=start - QPoint(0, 1000))
    assert json_widget.height() == json_widget._height_for_rows(1)
    # a dragged height is kept (no automatic fitting on a new value)
    json_widget.state = list(range(50))
    assert json_widget.height() == json_widget._height_for_rows(1)


def test_tab_moves_the_focus(qtbot):
    widget = make(qtbot)
    assert widget.widget.widgets["anything"].tabChangesFocus()


@pytest.mark.parametrize("text, value", [
    ("2", 2),
    ('"2"', "2"),
    ("[1,2]", [1, 2]),
    ('[1, "2"]', [1, "2"]),
    ('{"as":2}', {"as": 2}),
])
def test_any_field_end_to_end(text, value, qtbot):
    """typed into the `Any` field -> the model gets the value with its JSON type (2 is int, "2" is str)."""
    widget = make(qtbot)
    edit(widget.widget.widgets["anything"], text)
    model = to_model(widget)
    assert model.anything == value
    assert type(model.anything) is type(value)
    assert widget.is_valid()

    # and back: a model instance with that value shows it again
    roundtrip = make(qtbot, model)
    assert roundtrip.widget.widgets["anything"].toPlainText() == JsonSchemaWidget.format(value)
    assert to_model(roundtrip) == model


def test_any_field_invalid_input_keeps_the_model_value(qtbot):
    """`{"as"}` is no valid JSON: the model keeps the last valid value of the `Any` field."""
    widget = make(qtbot)
    json_widget = widget.widget.widgets["anything"]
    edit(json_widget, '{"as":2}')
    edit(json_widget, '{"as"}')
    assert json_widget.is_marked_invalid()
    assert to_model(widget).anything == {"as": 2}
