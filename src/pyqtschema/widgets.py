from functools import partial
from typing import List
from typing import Tuple, Optional, Dict

from PyQt5 import QtWidgets, QtCore, QtGui

from pyqtschema.widgets import SchemaWidgetMixin
from .utils import iter_layout_widgets, state_property, is_concrete_schema


class ObjectSchemaWidget(SchemaWidgetMixin, QtWidgets.QGroupBox):

    def __init__(self, schema: dict, ui_schema: dict, widget_builder: 'WidgetBuilder'):
        super().__init__(schema, ui_schema, widget_builder)

        self.widgets = self.populate_from_schema(schema, ui_schema, widget_builder)

    @state_property
    def state(self) -> dict:
        return {k: w.state for k, w in self.widgets.items()}

    @state.setter
    def state(self, state: dict):
        for name, value in state.items():
            self.widgets[name].state = value

    def handle_error(self, path: Tuple[str], err: Exception):
        name, *tail = path
        self.widgets[name].handle_error(tail, err)

    def widget_on_changed(self, name: str, value):
        self.state[name] = value
        self.on_changed.emit(self.state)

    def populate_from_schema(self, schema: dict, ui_schema: dict, widget_builder: 'WidgetBuilder'
                             ) -> Dict[str, QtWidgets.QWidget]:
        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setFlat(False)

        if 'title' in schema:
            self.setTitle(schema['title'])

        if 'description' in schema:
            self.setToolTip(schema['description'])

        # Populate rows
        widgets = {}

        for name, sub_schema in schema['properties'].items():
            sub_ui_schema = ui_schema.get(name, {})
            widget = widget_builder.create_widget(sub_schema, sub_ui_schema)  # TODO onchanged
            widget.on_changed.connect(partial(self.widget_on_changed, name))
            label = sub_schema.get("title", name)
            layout.addRow(label, widget)
            widgets[name] = widget

        return widgets


class FormWidget(QtWidgets.QWidget):

    def __init__(self, widget: SchemaWidgetMixin):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.error_widget = QtWidgets.QGroupBox()
        self.error_widget.setTitle("Errors")
        self.error_layout = QtWidgets.QVBoxLayout()
        self.error_widget.setLayout(self.error_layout)
        self.error_widget.hide()

        layout.addWidget(self.error_widget)
        layout.addWidget(widget)

        self.widget = widget

    def display_errors(self, errors: List[Exception]):
        self.error_widget.show()

        layout = self.error_widget.layout()
        while True:
            item = layout.takeAt(0)
            if not item:
                break
            item.widget().deleteLater()

        for err in errors:
            widget = QtWidgets.QLabel(f"<b>.{'.'.join(err.path)}</b> {err.message}")
            layout.addWidget(widget)

    def clear_errors(self):
        self.error_widget.hide()
