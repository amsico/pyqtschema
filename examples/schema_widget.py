"""SchemaWidget: a JSON-schema (from pydantic) plus optional data and a custom widget."""
import sys

from pydantic import BaseModel, Field
from qtpy.QtWidgets import QApplication, QHBoxLayout, QLabel

from pyqtschema import CustomObjectWidget, SchemaWidget, WidgetRegistry


class UnitValue(BaseModel):
    value: float = 0.0
    unit: str = "m"


class Limits(BaseModel):
    name: str = Field(default='dummy', description='stored in name-column')
    upper: UnitValue = UnitValue(value=10)
    lower: UnitValue = UnitValue()


class UnitValueWidget(CustomObjectWidget):
    """Value and unit in one row."""

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(self.schema.get("title", ""), self))
        layout.addWidget(self.build_field("value"), 3)
        layout.addWidget(self.build_field("unit"), 1)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    registry = WidgetRegistry()
    registry.register("unit-value", UnitValueWidget, ref="UnitValue")

    widget = SchemaWidget(Limits.model_json_schema(), data={"upper": {"value": 42}}, registry=registry)
    widget.on_changed.connect(print)
    widget.show()
    app.exec_()
