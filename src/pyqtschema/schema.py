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

    def validator(self):
        return self.validator_cls(self.schema)

    def resolve_schema(self, schema: Dict) -> Dict:
        """ resolve reference schema """
        if is_ref(schema):
            ident = schema['$ref']
            _first, definition, key = ident.split('/')
            return self.schema[definition][key]

        return schema
