"""Tests for the schema preparation helpers."""
import pytest

from pyqtschema.schema import (NULLABLE_KEY, Schema, is_nullable, normalize_schema, nullable_inner,
                               translate_schema)


def test_nullable_type_list_is_marked():
    schema = {"type": "object", "properties": {
        "a": {"type": ["string", "null"]},
        "b": {"type": ["null"]},
        "c": {"type": ["string", "integer"]},
    }}
    out = normalize_schema(schema)
    assert out["properties"]["a"] == {"type": ["string", "null"], NULLABLE_KEY: True}
    assert out["properties"]["b"]["type"] == "string"
    assert out["properties"]["c"] == {"type": ["string", "integer"]}
    assert NULLABLE_KEY not in schema["properties"]["a"]  # deep copy


def test_any_of_null_with_simple_type_is_merged_into_type_list():
    """pydantic `int | None = Field(None, ge=0)` - equivalent type-list, specific errors."""
    node = {"anyOf": [{"type": "integer", "minimum": 0}, {"type": "null"}], "default": None, "title": "N"}
    assert normalize_schema(node) == {"type": ["integer", "null"], "minimum": 0, "default": None,
                                      "title": "N", NULLABLE_KEY: True}


def test_any_of_null_with_ref_is_marked():
    node = {"anyOf": [{"$ref": "#/$defs/Unit"}, {"type": "null"}], "default": None, "title": "Lower"}
    assert normalize_schema(node) == {**node, NULLABLE_KEY: True}


def test_any_of_null_with_enum_is_not_merged():
    """`enum` applies to every type - merging would reject null."""
    node = {"anyOf": [{"type": "string", "enum": ["a", "b"]}, {"type": "null"}]}
    assert normalize_schema(node) == {**node, NULLABLE_KEY: True}


def test_any_of_keeps_remaining_alternatives():
    node = {"anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}]}
    assert normalize_schema(node) == {**node, NULLABLE_KEY: True}


def test_any_of_without_null_is_untouched():
    node = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
    assert normalize_schema(node) == node


@pytest.mark.parametrize("node, inner", [
    ({"type": ["integer", "null"], "minimum": 0, NULLABLE_KEY: True}, {"type": "integer", "minimum": 0}),
    ({"anyOf": [{"$ref": "#/$defs/U"}, {"type": "null"}], "title": "X", "default": None, NULLABLE_KEY: True},
     {"$ref": "#/$defs/U", "title": "X"}),
    ({"anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}], NULLABLE_KEY: True},
     {"anyOf": [{"type": "string"}, {"type": "integer"}]}),
    ({"type": ["string", "null"], "default": "x", NULLABLE_KEY: True}, {"type": "string", "default": "x"}),
])
def test_nullable_inner(node, inner):
    assert is_nullable(node)
    assert nullable_inner(node) == inner


def test_normalized_schema_accepts_null():
    """the validation is unchanged: a nullable field still accepts None."""
    schema = normalize_schema({"type": "object", "properties": {
        "a": {"anyOf": [{"type": "integer", "minimum": 0}, {"type": "null"}]},
        "b": {"anyOf": [{"$ref": "#/$defs/U"}, {"type": "null"}]}},
        "$defs": {"U": {"type": "object"}}})
    assert Schema(schema).is_valid_data({"a": None, "b": None})
    assert not Schema(schema).is_valid_data({"a": -1, "b": None})


def test_translate_schema():
    schema = {"title": "Root", "properties": {"a": {"title": "A", "description": "Desc", "default": "A"}}}
    out = translate_schema(schema, str.upper)
    assert out["title"] == "ROOT"
    assert out["properties"]["a"] == {"title": "A".upper(), "description": "DESC", "default": "A"}
    assert translate_schema(schema, None) == schema
