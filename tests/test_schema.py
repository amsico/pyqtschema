from pyqtschema.schema import Schema


def test_init_schema():
    _def = {
        "title": "Simple",
        "type": "object",
        "properties": {
            "string": {"title": "String", "type": "string"},
            "boolean": {"title": "Boolean", "default": True, "type": "boolean"},
            "integer": {"title": "Integer", "default": 2, "type": "integer"},
            "number": {"title": "Number", "default": 2.2, "type": "number"}
        },
        "required": ["string"]
    }
    schema = Schema(_def)


def test_schema_is_valid():
    _def = {'type': 'object', 'properties': {'checker': {'type': 'string'}},
            'schema': {'additionalProperties': False}, 'additionalProperties': False}
    schema = Schema(_def)

    assert schema.is_valid_data({'checker': 'a string'})
    assert schema.is_valid_data({'checker': ''})

    assert schema.is_valid_data({'checker': 1}) is False
    assert schema.is_valid_data({'checker': 1.2}) is False

    assert schema.is_valid_data({'invalid_name': 1}) is False
    assert schema.is_valid_data({'invalid_name': "1"}) is False
