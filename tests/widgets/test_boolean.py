import pytest
from PyQt5.QtCore import Qt

from pyqtschema.widgets import CheckboxSchemaWidget


@pytest.fixture
def schema():
    return {}


def test_checkbox_state(schema, builder, qtbot):
    widget = CheckboxSchemaWidget(schema, {}, builder)
    qtbot.addWidget(widget)

    widget.state = True
    assert widget.isChecked()

    widget.state = False
    assert widget.isChecked() is False


def test_checkbox_via_api(schema, builder, qtbot):
    widget = CheckboxSchemaWidget(schema, {}, builder)
    qtbot.addWidget(widget)

    widget.setChecked(False)
    assert widget.state is False

    widget.setChecked(True)
    assert widget.state is True


def test_checkbox_click(schema, builder, qtbot):
    widget = CheckboxSchemaWidget(schema, {}, builder)
    qtbot.addWidget(widget)
    widget.show()

    widget.setChecked(False)
    assert not widget.state

    with qtbot.waitExposed(widget, timeout=500):
        qtbot.mouseClick(widget, Qt.LeftButton)

    assert widget.state
