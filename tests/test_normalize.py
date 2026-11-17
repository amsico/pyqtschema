"""Tests for the schema preparation helpers."""
from pyqtschema.schema import normalize_schema, translate_schema


def test_nullable_type_list():
    schema = {"type": "object", "properties": {
        "a": {"type": ["string", "null"]},
        "b": {"type": ["null"]},
        "c": {"type": ["string", "integer"]},
    }}
    out = normalize_schema(schema)
    assert out["properties"]["a"]["type"] == "string"
    assert out["properties"]["b"]["type"] == "string"
    assert out["properties"]["c"]["type"] == ["string", "integer"]
    assert schema["properties"]["a"]["type"] == ["string", "null"]  # deep copy


def test_any_of_null_branch_is_unwrapped():
    node = {"anyOf": [{"$ref": "#/$defs/Unit"}, {"type": "null"}], "default": None, "title": "Lower"}
    out = normalize_schema(node)
    assert out == {"$ref": "#/$defs/Unit", "default": None, "title": "Lower"}


def test_any_of_keeps_remaining_alternatives():
    node = {"anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}]}
    assert normalize_schema(node) == {"anyOf": [{"type": "string"}, {"type": "integer"}]}


def test_any_of_without_null_is_untouched():
    node = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
    assert normalize_schema(node) == node


def test_translate_schema():
    schema = {"title": "Root", "properties": {"a": {"title": "A", "description": "Desc", "default": "A"}}}
    out = translate_schema(schema, str.upper)
    assert out["title"] == "ROOT"
    assert out["properties"]["a"] == {"title": "A".upper(), "description": "DESC", "default": "A"}
    assert translate_schema(schema, None) == schema
