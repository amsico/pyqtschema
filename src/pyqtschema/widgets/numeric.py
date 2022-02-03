from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QSlider

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property


def range_from_schema(schema: dict):
    # https://json-schema.org/understanding-json-schema/reference/numeric.html#range
    # there should be an exclusive-minimum OR a minimum
    minimum = schema.get('exclusiveMinimum', schema.get('minimum', None))
    maximum = schema.get('exclusiveMaximum', schema.get('maximum', None))
    return minimum, maximum


class SpinSchemaWidget(SchemaWidgetMixin, QSpinBox):

    @state_property
    def state(self) -> int:
        return self.value()

    @state.setter
    def state(self, state: int):
        self.setValue(state)

    def configure(self):
        self.valueChanged.connect(self.on_changed.emit)

        minimum, maximum = range_from_schema(self.schema)
        if maximum:
            self.setMaximum(maximum)
        if minimum:
            self.setMinimum(minimum)

        if "multipleOf" in self.schema:
            self.setSingleStep(self.schema["multipleOf"])


class SpinDoubleSchemaWidget(SchemaWidgetMixin, QDoubleSpinBox):

    @state_property
    def state(self) -> float:
        return self.value()

    @state.setter
    def state(self, state: float):
        self.setValue(state)

    def configure(self):
        self.valueChanged.connect(self.on_changed.emit)

        minimum, maximum = range_from_schema(self.schema)
        if maximum:
            self.setMaximum(maximum)
        if minimum:
            self.setMinimum(minimum)

        if "multipleOf" in self.schema:
            self.setSingleStep(self.schema["multipleOf"])


class IntegerRangeSchemaWidget(SchemaWidgetMixin, QSlider):

    def __init__(self, schema: dict, ui_schema: dict, widget_builder: 'WidgetBuilder', *args, **kwargs):
        kwargs['orientation'] = Qt.Horizontal
        super().__init__(schema, ui_schema, widget_builder, *args, **kwargs)

    @state_property
    def state(self) -> int:
        return self.value()

    @state.setter
    def state(self, state: int):
        self.setValue(state)

    def configure(self):
        self.valueChanged.connect(self.on_changed.emit)
        schema = self.schema

        minimum, maximum = range_from_schema(schema)

        multiple_of = schema.get('multipleOf', None)
        if multiple_of:
            self.setTickInterval(multiple_of)
            self.setSingleStep(multiple_of)
            self.setTickPosition(self.TicksBothSides)

        if minimum is None or maximum is None:
            raise ValueError('Cannot create a slider without boundary conditions')
        self.setRange(minimum, maximum)
