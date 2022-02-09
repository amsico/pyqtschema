import pytest

from pyqtschema.widgets import FilepathSchemaWidget, DirectoryPathSchemaWidget


@pytest.mark.parametrize('cls', [FilepathSchemaWidget, DirectoryPathSchemaWidget])
def test_path_init(cls, builder, qtbot):
    schema = {}
    widget = cls(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)
