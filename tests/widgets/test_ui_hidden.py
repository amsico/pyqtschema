import pytest

# see also issue https://github.com/amsico/pyqtschema/issues/12
from pydantic import BaseModel

from pyqtschema.utils import build_example_widget


class Simple(BaseModel):
    string: str
    integer: int


class SubSchema(BaseModel):
    name: str
    sub: Simple


schema = Simple.schema()
sub_schema = SubSchema.schema()


def test_hide_widget(qtbot):
    ui_schema = {'string': {'ui:hidden': True}}
    widget = build_example_widget(schema, ui_schema=ui_schema)
    widget.show()
    qtbot.addWidget(widget)
    assert not widget.widget.widgets['string'].isVisible()
    assert widget.widget.widgets['integer'].isVisible()

    assert widget.widget.widgets['string'].isEnabled()
    assert widget.widget.widgets['integer'].isEnabled()


def test_disable_widget(qtbot):
    ui_schema = {'integer': {'ui:disabled': True}}
    widget = build_example_widget(schema, ui_schema=ui_schema)
    widget.show()
    qtbot.addWidget(widget)
    assert widget.widget.widgets['string'].isVisible()
    assert widget.widget.widgets['integer'].isVisible()

    assert widget.widget.widgets['string'].isEnabled()
    assert not widget.widget.widgets['integer'].isEnabled()


def test_hide_widget_sub(qtbot):
    ui_schema = {'sub': {'string': {'ui:hidden': True}}}
    widget = build_example_widget(sub_schema, ui_schema=ui_schema)
    widget.show()
    qtbot.addWidget(widget)

    assert widget.widget.widgets['name'].isVisible()
    assert widget.widget.widgets['sub'].isVisible()
    assert widget.widget.widgets['sub'].widgets['integer'].isVisible()

    assert not widget.widget.widgets['sub'].widgets['string'].isVisible()
