"""
Regression tests: unknown string-``format`` values must not crash the builder.

Pydantic emits `format: "date-time"` / `"date"` / `"uri"` ... on string fields.
Previously ``WidgetBuilder.create_widget`` raised a ``KeyError`` for these
formats and for unknown ``ui:widget`` variants.
"""
from pyqtschema.builder import WidgetBuilder
from pyqtschema.widgets import TextSchemaWidget


def _build(schema, ui_schema=None, state=None):
    return WidgetBuilder(schema).create_form(ui_schema, state)


def test_unknown_format_does_not_raise(qtbot):
    schema = {
        "type": "object",
        "properties": {
            "stamp": {"type": "string", "format": "date-time"},
            "day": {"type": "string", "format": "date"},
            "url": {"type": "string", "format": "uri"},
        },
    }
    form = _build(schema)
    qtbot.addWidget(form)
    assert isinstance(form.state, dict)
    assert set(form.state) == {"stamp", "day", "url"}


def test_unknown_format_uses_text_widget(qtbot):
    schema = {
        "type": "object",
        "properties": {
            "day": {"type": "string", "format": "date"},
        },
    }
    form = _build(schema)
    qtbot.addWidget(form)
    text_widgets = form.widget.findChildren(TextSchemaWidget)
    assert text_widgets, "a string field with an unknown format should use the text-widget"


def test_pydantic_datetime_field(qtbot):
    from datetime import datetime

    from pydantic import BaseModel, Field

    class Model(BaseModel):
        created: datetime = Field(default_factory=datetime.now)
        label: str = Field(default="x")

    form = _build(Model.model_json_schema())
    qtbot.addWidget(form)
    assert "created" in form.state
    assert "label" in form.state


def test_unknown_ui_widget_falls_back(qtbot):
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    form = WidgetBuilder(schema).create_form({"name": {"ui:widget": "does-not-exist"}})
    qtbot.addWidget(form)
    assert "name" in form.state