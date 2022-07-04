from enum import Enum

import pytest

from pyqtschema import WidgetBuilder
from pyqtschema.widgets import EnumSchemaWidget


class Units(Enum):
    none = '1'
    meter = 'm'
    seconds = 's'


schema_enum = {
    'title': 'UnitValue',
    'type': 'object',
    'properties': {
        'value': {'title': 'Value', 'type': 'number'},
        'unit': {'default': '1', '$ref': '#/definitions/Units'}
    },
    'required': ['value', 'unit'],
    'definitions': {'Units': {'title': 'Units', 'description': 'An enumeration.', 'enum': ['1', 'm', 's']}}
}


def test_enum_init(qtbot):
    builder = WidgetBuilder(schema_enum)
    sub_schema = schema_enum['definitions']['Units']
    widget = EnumSchemaWidget(sub_schema, {}, builder)

    assert widget.count() == 3


def test_enum_set_values(qtbot):
    builder = WidgetBuilder(schema_enum)
    sub_schema = schema_enum['definitions']['Units']
    widget = EnumSchemaWidget(sub_schema, {}, builder)

    widget.state = '1'
    assert widget.currentText() == '1'

    widget.state = 's'
    assert widget.currentText() == 's'


def test_enum_set_enum(qtbot):
    builder = WidgetBuilder(schema_enum)
    sub_schema = schema_enum['definitions']['Units']
    widget = EnumSchemaWidget(sub_schema, {}, builder)

    widget.state = Units.none
    assert widget.currentText() == '1'

    widget.state = Units.seconds
    assert widget.currentText() == 's'
