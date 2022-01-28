from pyqtschema.widgets.utils import is_concrete_schema


def test_is_concrete_schema():
    assert not is_concrete_schema({'non': 'sense'})
    assert not is_concrete_schema({'type': 'string'})
