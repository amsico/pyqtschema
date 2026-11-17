"""JSON-schema handling (Qt-free).

* :class:`Schema` - validation, reference resolution and default values.
* :func:`normalize_schema` - mark nullable fields (``Optional`` in pydantic)
  with ``x-nullable``; they are rendered with a checkbox for ``None``.
* :func:`nullable_inner` - the editable (non-null) part of a nullable field.
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

#: schema-keyword marking a node as nullable (set by :func:`normalize_schema`):
#: the node accepts ``null`` and is rendered with a checkbox for ``None``
NULLABLE_KEY = "x-nullable"

#: keywords applying to every type: a branch with one of them cannot be merged
#: into a ``"type": [<type>, "null"]``-list without changing the meaning
_ALL_TYPE_KEYWORDS = ("enum", "const", "$ref", "anyOf", "oneOf", "allOf", "not", "if")


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
        return {k: self.compute_defaults(s) for k, s in schema.get("properties", {}).items()}

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

        if schema.get(NULLABLE_KEY):
            # nullable without default: starts as None (checkbox unchecked)
            return None

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
    """Deep-copy ``schema`` and mark nullable constructs with ``x-nullable``.

    A nullable node keeps accepting ``null`` (validation is unchanged); the
    widget-builder renders it with a checkbox for ``None`` around the widget
    of its editable part (see :func:`nullable_inner`):

    * ``"type": ["string", "null"]`` is marked; a pure ``["null"]`` falls back
      to ``"string"`` (nothing else to edit).
    * ``anyOf``/``oneOf`` with ``{"type": "null"}``-alternatives (pydantic:
      ``int | None``) are marked.  A single remaining alternative with a plain
      ``type`` is merged into a ``type``-list (``{"type": ["integer", "null"],
      "minimum": 0}``) - equivalent, but the validation-errors name the
      violated keyword instead of "not valid under any of the given schemas".
      Keys of the node itself (``title``, ``default``, ...) are kept.
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


def _is_null(alt) -> bool:
    return isinstance(alt, dict) and alt.get("type") == "null"


def _normalize_node(node: SchemaNode) -> None:
    raw = node.get("type")
    if isinstance(raw, list) and "null" in raw:
        non_null = [t for t in raw if t != "null"]
        if non_null:
            node[NULLABLE_KEY] = True
        else:
            node["type"] = "string"

    for key in ("anyOf", "oneOf"):
        alts = node.get(key)
        if not isinstance(alts, list) or not any(_is_null(alt) for alt in alts):
            continue
        kept = [alt for alt in alts if not _is_null(alt)]
        if not kept or any(alt == {} for alt in kept):
            # nothing left, or an unrestricted branch (`Optional[Any]`): the node
            # accepts any value - including null, no checkbox needed
            node.pop(key)
            continue
        node[NULLABLE_KEY] = True
        branch = kept[0]
        if (len(kept) == 1 and isinstance(branch, dict) and isinstance(branch.get("type"), str)
                and not any(k in branch for k in _ALL_TYPE_KEYWORDS) and "type" not in node):
            node.pop(key)
            for k, v in branch.items():
                node.setdefault(k, v)
            node["type"] = [branch["type"], "null"]


def is_nullable(node: SchemaNode) -> bool:
    """Whether ``node`` was marked nullable by :func:`normalize_schema`."""
    return isinstance(node, dict) and node.get(NULLABLE_KEY) is True


def nullable_inner(node: SchemaNode) -> SchemaNode:
    """The editable part of a nullable node: ``null`` removed.

    ``{"type": ["integer", "null"], "minimum": 0}`` -> ``{"type": "integer", "minimum": 0}``;
    ``{"anyOf": [{"$ref": ...}, {"type": "null"}], "title": "X"}`` -> ``{"$ref": ..., "title": "X"}``.
    A ``default`` of ``None`` is dropped (the inner widget starts with its own default).
    """
    inner = {k: v for k, v in node.items() if k != NULLABLE_KEY}
    if "default" in inner and inner["default"] is None:
        inner.pop("default")

    raw = inner.get("type")
    if isinstance(raw, list):
        non_null = [t for t in raw if t != "null"]
        inner["type"] = non_null[0] if len(non_null) == 1 else non_null

    for key in ("anyOf", "oneOf"):
        alts = inner.get(key)
        if not isinstance(alts, list):
            continue
        kept = [alt for alt in alts if not _is_null(alt)]
        if len(kept) == 1 and isinstance(kept[0], dict):
            inner.pop(key)
            for k, v in kept[0].items():
                inner.setdefault(k, v)
        else:
            inner[key] = kept
    return inner
