"""JSON-schema handling (Qt-free).

* :class:`Schema` - validation, reference resolution and default values.
* :func:`normalize_schema` - reduce constructs the widgets cannot build to
  equivalent buildable ones (nullable ``type``-lists and ``null``-branches in
  ``anyOf``/``oneOf`` as emitted for ``Optional`` fields by pydantic).
* :func:`translate_schema` - apply a translator to ``title``/``description``.
"""
from copy import deepcopy
from pathlib import Path
from json import load
from typing import Any, Callable, Dict, Optional

from jsonschema.validators import validator_for, validate

#: A JSON-schema node as plain dict: either the root schema or any
#: sub-schema of it (a property, an ``items`` entry, an ``anyOf`` branch, ...).
#: A node may be a reference of the form ``{"$ref": "#/definitions/<name>", ...}``
#: which points into the ``definitions`` of the root schema; keys next to
#: ``$ref`` (``title``, ``description``, ``default``, ...) are called siblings.
SchemaNode = Dict[str, Any]


def validate_schema_definition(schema: Dict):
    """ TODO: validate the schema itself """


def schema_from_json(path: Path):
    with open(path, 'r') as _input:
        schema = load(_input)
    validate_schema_definition(schema)
    return schema


def is_ref(schema: dict):
    return '$ref' in schema


class Schema:
    """ Combines schema-related functionality """

    def __init__(self, schema: Dict, validator_cls=None):
        self.schema: Dict = schema

        if validator_cls is None:
            validator_cls = validator_for(schema)
        self.validator_cls = validator_cls
        self.check_schema()

    def check_schema(self):
        self.validator_cls.check_schema(self.schema)

    def is_valid_data(self, data):
        try:
            validate(data, self.schema)
            return True
        except Exception:
            return False

    def validator(self, schema: Dict = None):
        if schema is None:
            schema = self.schema
        return self.validator_cls(schema)

    def resolve_schema(self, schema: SchemaNode) -> SchemaNode:
        """ resolve a reference node to the definition it points to

        Siblings of ``$ref`` take precedence over the referenced definition.
        Nested references are followed (cycle-guarded); a node without
        ``$ref`` is returned unchanged.
        """
        seen = set()
        while is_ref(schema):
            ident = schema['$ref']
            if ident in seen:
                break
            seen.add(ident)
            _first, definition, key = ident.split('/')
            target = self.schema[definition][key]
            siblings = {k: v for k, v in schema.items() if k != '$ref'}
            schema = {**target, **siblings} if siblings else target

        return schema

    def definitions(self):
        return self.schema.get('definitions', {})

    @staticmethod
    def _enum_defaults(schema):
        try:
            return schema["enum"][0]
        except IndexError:
            return None

    def _object_defaults(self, schema):
        return {k: self.compute_defaults(s) for k, s in schema["properties"].items()}

    def _any_of_defaults(self, schema, definitions: Dict = None):
        out = [self.compute_defaults(s) for s in schema["anyOf"]]
        return out

    def _array_defaults(self, schema):
        # be robust against a missing 'items' key (arrays without an
        # item-schema): fall back to an empty array-default instead of a KeyError
        items_schema = schema.get('items')
        if not isinstance(items_schema, list):
            return []
        return [self.compute_defaults(s) for s in items_schema]

    def compute_defaults(self, schema):
        schema = self.resolve_schema(schema)

        if "default" in schema:
            return schema["default"]

        if 'anyOf' in schema:
            return self._any_of_defaults(schema)

        if "enum" in schema:
            return self._enum_defaults(schema)

        schema_type = schema.get("type")

        if schema_type == "object":
            return self._object_defaults(schema)

        elif schema_type == "array":
            return self._array_defaults(schema)

        return None


Translator = Callable[[str], str]


def normalize_schema(schema: SchemaNode) -> SchemaNode:
    """Deep-copy ``schema`` and normalize nullable constructs.

    * ``"type": ["string", "null"]`` -> ``"type": "string"``; a pure
      ``["null"]`` falls back to ``"string"`` (nothing else to edit).
    * ``anyOf``/``oneOf`` alternatives of ``{"type": "null"}`` are dropped; a
      single remaining alternative is unwrapped into the node (its keys do not
      override keys of the node itself, e.g. ``title``/``default``).
    """
    out = deepcopy(schema)
    _walk(out, _normalize_node)
    return out


def translate_schema(schema: SchemaNode, translator: Optional[Translator]) -> SchemaNode:
    """Deep-copy ``schema`` and translate every ``title``/``description``."""
    out = deepcopy(schema)
    if translator is None:
        return out

    def _translate(node: SchemaNode) -> None:
        for key in ("title", "description"):
            value = node.get(key)
            if isinstance(value, str):
                node[key] = translator(value)

    _walk(out, _translate)
    return out


def _walk(node, visit: Callable[[SchemaNode], None]) -> None:
    if isinstance(node, dict):
        for child in list(node.values()):
            _walk(child, visit)
        visit(node)
    elif isinstance(node, list):
        for child in node:
            _walk(child, visit)


def _normalize_node(node: SchemaNode) -> None:
    raw = node.get("type")
    if isinstance(raw, list):
        non_null = [t for t in raw if t != "null"]
        if len(non_null) == 1:
            node["type"] = non_null[0]
        elif not non_null:
            node["type"] = "string"

    for key in ("anyOf", "oneOf"):
        alts = node.get(key)
        if not isinstance(alts, list):
            continue
        kept = [alt for alt in alts if not (isinstance(alt, dict) and alt.get("type") == "null")]
        if len(kept) == len(alts):
            continue
        if not kept:
            node.pop(key)
        elif len(kept) == 1 and isinstance(kept[0], dict):
            node.pop(key)
            for k, v in kept[0].items():
                node.setdefault(k, v)
        else:
            node[key] = kept
