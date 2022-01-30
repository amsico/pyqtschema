from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QSlider

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property


class SpinSchemaWidget(SchemaWidgetMixin, QSpinBox):

    @state_property
    def state(self) -> int:
        return self.value()

    @state.setter
    def state(self, state: int):
        self.setValue(state)

    def configure(self):
        self.valueChanged.connect(self.on_changed.emit)

        if "maximum" in self.schema:
            if "exclusiveMaximum" in self.schema:
                self.setMaximum(min(self.schema["maximum"], self.schema["exclusiveMaximum"] - 1))
            else:
                self.setMaximum(self.schema["maximum"])
        elif "exclusiveMaximum" in self.schema:
            self.setMaximum(self.schema["exclusiveMaximum"] - 1)
        if "minimum" in self.schema:
            if "exclusiveMinimum" in self.schema:
                self.setMinimum(min(self.schema["minimum"], self.schema["exclusiveMinimum"] + 1))
            else:
                self.setMinimum(self.schema["minimum"])
        elif "exclusiveMinimum" in self.schema:
            self.setMinimum(self.schema["exclusiveMinimum"] + 1)
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

        if "maximum" in self.schema:
            if "exclusiveMaximum" in self.schema:
                self.setMaximum(min(self.schema["maximum"], self.schema["exclusiveMaximum"]))
            else:
                self.setMaximum(self.schema["maximum"])
        elif "exclusiveMaximum" in self.schema:
            self.setMaximum(self.schema["exclusiveMaximum"])
        if "minimum" in self.schema:
            if "exclusiveMinimum" in self.schema:
                self.setMinimum(min(self.schema["minimum"], self.schema["exclusiveMinimum"]))
            else:
                self.setMinimum(self.schema["minimum"])
        elif "exclusiveMinimum" in self.schema:
            self.setMinimum(self.schema["exclusiveMinimum"])
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

        minimum = 0
        if "minimum" in self.schema:
            minimum = self.schema["minimum"]
            if self.schema.get("exclusiveMinimum"):
                minimum += 1

        maximum = 0
        if "maximum" in self.schema:
            maximum = self.schema["maximum"]
            if self.schema.get("exclusiveMaximum"):
                maximum -= 1

        if "multipleOf" in self.schema:
            self.setTickInterval(self.schema["multipleOf"])
            self.setSingleStep(self.schema["multipleOf"])
            self.setTickPosition(self.TicksBothSides)

        self.setRange(minimum, maximum)
