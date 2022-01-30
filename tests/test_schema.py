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
