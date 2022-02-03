from collections import OrderedDict
from functools import partial
from typing import Tuple, Dict

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGroupBox, QWidget, QGridLayout, QLabel, QVBoxLayout, QComboBox

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property
from pyqtschema.widgets.utils import iter_layout_widgets


class ObjectSchemaWidget(SchemaWidgetMixin, QGroupBox):

    def __init__(self, schema: dict, ui_schema: dict, widget_builder: 'WidgetBuilder', *args, **kwargs):
        super().__init__(schema, ui_schema, widget_builder, *args, **kwargs)

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
                             ) -> Dict[str, QWidget]:
        # layout = QFormLayout()
        layout = QGridLayout()
        self.setLayout(layout)
        layout.setAlignment(Qt.AlignTop)
        self.setFlat(False)

        if 'title' in schema:
            self.setTitle(schema['title'])

        if 'description' in schema:
            self.setToolTip(schema['description'])

        # Populate rows
        widgets = {}

        for name, sub_schema in schema['properties'].items():
            sub_ui_schema = ui_schema.get(name, {})

            _hide = sub_ui_schema.get('ui:hidden', False)
            _disable = sub_ui_schema.get('ui:disabled', False)

            widget = widget_builder.create_widget(sub_schema, sub_ui_schema, parent=self)  # TODO onchanged
            widget.on_changed.connect(partial(self.widget_on_changed, name))
            widget.setHidden(_hide)
            widget.setDisabled(_disable)

            _row_index = layout.rowCount()
            if widget.show_title():
                label = sub_schema.get("title", name)
                _lbl = QLabel(label, parent=self)
                _lbl.setHidden(_hide)
                _lbl.setDisabled(_disable)

                layout.addWidget(_lbl, _row_index, 0)
                layout.addWidget(widget, _row_index, 1)
            else:
                layout.addWidget(widget, _row_index, 0, 1, 2)
            widgets[name] = widget

        return widgets
