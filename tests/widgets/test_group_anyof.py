from pyqtschema.builder import WidgetBuilder
from pyqtschema.widgets.any_of import AnyOfSchemaWidget

schema = {
    "title": "SimpleAnyOf",
    "type": "object",
    "properties": {"value": {
        "title": "Value",
        "anyOf": [{"type": "string"}, {"type": "integer"}]
    }
    },
    "required": ["value"]
}


def test_any_of_init(qtbot):
    builder = WidgetBuilder(schema)
    sub_schema = schema['properties']['value']
    widget = AnyOfSchemaWidget(sub_schema, {}, builder)

    assert widget.state == ""


def test_any_of_set_state(qtbot):
    builder = WidgetBuilder(schema)
    sub_schema = schema['properties']['value']
    widget = AnyOfSchemaWidget(sub_schema, {}, builder)

    value = 'Hi there'
    widget.state = value
    assert widget.state == value
    assert widget.widgets['string'].state == value
