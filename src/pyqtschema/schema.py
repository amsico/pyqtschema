from pathlib import Path
from json import load, dump
from typing import Dict

from jsonschema import Draft7Validator
from jsonschema.validators import validator_for


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
    """ Combines schema-related functinoality """

    def __init__(self, schema: Dict, validator_cls=None):
        self.schema: Dict = schema

        if validator_cls is None:
            validator_cls = validator_for(schema)
        self.validator_cls = validator_cls
        self.check_schema()

    def check_schema(self):
        self.validator_cls.check_schema(self.schema)

    def validator(self, schema: Dict = None):
        if schema is None:
            schema = self.schema
        return self.validator_cls(schema)

    def resolve_schema(self, schema: Dict) -> Dict:
        """ resolve reference schema """
        if is_ref(schema):
            ident = schema['$ref']
            _first, definition, key = ident.split('/')
            return self.schema[definition][key]

        return schema

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
        items_schema = schema['items']
        if isinstance(items_schema, dict):
            return []

        return [self.compute_defaults(s) for s in schema["items"]]

    def compute_defaults(self, schema):
        schema = self.resolve_schema(schema)

        if "default" in schema:
            return schema["default"]

        if 'anyOf' in schema:
            return self._any_of_defaults(schema)

        if "enum" in schema:
            return self._enum_defaults(schema)

        schema_type = schema["type"]

        if schema_type == "object":
            return self._object_defaults(schema)

        elif schema_type == "array":
            return self._array_defaults(schema)

        return None
