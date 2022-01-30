import pytest
from PyQt5.QtCore import Qt

from pyqtschema.widgets import TextSchemaWidget, TextAreaSchemaWidget, PasswordWidget


@pytest.mark.parametrize('cls', [TextSchemaWidget, TextAreaSchemaWidget, PasswordWidget])
def test_text_init(cls, builder, qtbot):
    schema = {}
    widget = cls(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)


@pytest.mark.parametrize('cls', [TextSchemaWidget, TextAreaSchemaWidget, PasswordWidget])
def test_text_state_write(cls, builder, qtbot):
    schema = {}
    widget = cls(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)

    txt = 'Hello widget'

    widget.state = txt
    if isinstance(widget, TextAreaSchemaWidget):
        assert widget.toPlainText() == txt
    else:
        assert widget.text() == txt


@pytest.mark.parametrize('cls', [TextSchemaWidget, TextAreaSchemaWidget, PasswordWidget])
def test_text_state_read(cls, builder, qtbot):
    schema = {}
    widget = cls(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)

    txt = 'Hello widget'

    widget.setText(txt)
    widget.state == txt
