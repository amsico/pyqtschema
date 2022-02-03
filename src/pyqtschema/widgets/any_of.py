from collections import OrderedDict
from functools import partial
from typing import Dict

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QGroupBox

from .base import state_property, SchemaWidgetMixin
from .utils import iter_layout_widgets


class AnyOfSchemaWidget(SchemaWidgetMixin, QGroupBox):

    def __init__(self, schema: dict, ui_schema: dict, widget_builder: 'WidgetBuilder', *args, **kwargs):
        self.select_combo: QComboBox = None
        self.items_group: QGroupBox = None

        super().__init__(schema, ui_schema, widget_builder, *args, **kwargs)

        self.widgets: OrderedDict = OrderedDict()
        self.populate_from_schema(schema, ui_schema, widget_builder)

    def configure(self):
        if 'title' in self.schema:
            self.setTitle(self.schema['title'])

        self.select_combo = QComboBox()
        self.select_combo.currentIndexChanged.connect(self.select_schema)

        lay = QVBoxLayout()
        self.items_group = QGroupBox()
        self.items_group.setLayout(lay)

        layout = QVBoxLayout()
        layout.addWidget(self.select_combo)
        layout.addWidget(self.items_group)
        self.setLayout(layout)

    def select_schema(self, idx: int):
        for iii, widget in enumerate(iter_layout_widgets(self.items_group.layout())):
            widget.setVisible(iii == idx)
        self.on_changed.emit(self.state)

    def populate_from_schema(self, schema: dict, ui_schema: dict, widget_builder: 'WidgetBuilder'
                             ) -> Dict[str, QWidget]:
        self.setFlat(False)

        widgets = self.widgets
        _combo_items = []
        for sub_schema in schema.get('anyOf', []):
            try:
                name = sub_schema['$ref']
                c_name = name.split('/')[-1]
            except KeyError:
                c_name = name = sub_schema['type']

            _combo_items.append(c_name)
            sub_ui_schema = ui_schema.get(name, {})

            widget = widget_builder.create_widget(sub_schema, sub_ui_schema, parent=self)  # TODO onchanged
            widgets[name] = widget
            widget.setVisible(False)

            widget.on_changed.connect(partial(self.widget_on_changed, name))
            if 'title' in schema:
                self.setTitle(schema['title'])

            if 'description' in schema:
                self.setToolTip(schema['description'])

            self.items_group.layout().addWidget(widget)

        self.select_combo.addItems(_combo_items)
        return widgets

    def widget_on_changed(self, name: str, value):
        # self.state[name] = value
        self.on_changed.emit(self.state)

    @state_property
    def state(self) -> dict:
        _idx = self.select_combo.currentIndex()
        _widgets = list(self.widgets.values())
        return _widgets[_idx].state

    @state.setter
    def state(self, state: dict):
        # assumption:
        #   state is dict => set the state to the current selection
        #   state is a list => set state to all widgets
        # Background:
        #   the function may be called after initializing the form including all defaults for any possible item
        _widgets = list(self.widgets.values())
        if isinstance(state, (list, tuple)):
            for idx, _dict in enumerate(state):
                _widgets[idx].state = _dict
        else:
            _idx = self.select_combo.currentIndex()
            _widgets[_idx].state = state

    def show_title(self) -> bool:
        return False
