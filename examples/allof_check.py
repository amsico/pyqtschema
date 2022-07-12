from pyqtschema import build_example

schema = {
    'title': 'AllOf example',
    'type': 'object',
    'properties':
        {
            'name': {'title': 'Example-name', 'type': 'string'},
            'rule': {'title': 'Rule', 'allOf': [{'$ref': '#/definitions/SubDef'}]}
        },
    'required': ['attribute'],
    'definitions': {
        'SubDef': {
            'title': 'SubTitle', 'type': 'object',
            'properties': {
                'checker_str': {'title': 'Checker', 'default': 'xyz', 'type': 'string'},
                'string': {'title': 'String', 'default': 'abc', 'type': 'string'}
            }
        }
    }
}

if __name__ == '__main__':
    build_example(schema)
