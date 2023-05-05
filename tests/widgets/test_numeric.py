import pytest
from qtpy.QtCore import Qt

from pyqtschema.widgets import SpinSchemaWidget, SpinDoubleSchemaWidget, IntegerRangeSchemaWidget


@pytest.mark.parametrize('cls', [SpinSchemaWidget, SpinDoubleSchemaWidget, IntegerRangeSchemaWidget])
def test_text_init(cls, builder, qtbot):
    schema = {}
    widget = cls(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)


@pytest.mark.parametrize('cls', [SpinSchemaWidget, SpinDoubleSchemaWidget, IntegerRangeSchemaWidget])
def test_text_state_write_int(cls, builder, qtbot):
    schema = {}
    widget = cls(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)

    value = 6
    with qtbot.waitSignal(widget.valueChanged, timeout=1000):
        widget.state = value
    assert widget.value() == value


@pytest.mark.parametrize('cls', [SpinSchemaWidget, SpinDoubleSchemaWidget, IntegerRangeSchemaWidget])
def test_text_state_read_int(cls, builder, qtbot):
    schema = {}
    widget = cls(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)

    value = 6
    with qtbot.waitSignal(widget.valueChanged, timeout=1000):
        widget.setValue(value)
    assert widget.state == value
