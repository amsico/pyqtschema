from collections import OrderedDict
from functools import partial
from typing import Dict, List

from qtpy.QtWidgets import QWidget, QVBoxLayout, QComboBox, QGroupBox

from ..schema import Schema
from .base import state_property, SchemaWidgetMixin
from .utils import iter_layout_widgets

CHECKER_KEY = 'checker'


def _any_of_schema(schema: dict, widget_builder: 'WidgetBuilder') -> List[Schema]:
    """ """
    out = []
    for _any in schema['anyOf']:
        _schema = {'type': 'object',
                   'properties': {
                       CHECKER_KEY: widget_builder.schema.resolve_schema(_any)
                   },
                   'definitions': widget_builder.schema.definitions(),
                   "schema": {
                       'additionalProperties': False,
                   },
                   'additionalProperties': False,
                   }
        out.append(Schema(_schema))

    return out


class AnyOfSchemaWidget(SchemaWidgetMixin, QGroupBox):

    def __init__(self, schema: dict, ui_schema: dict, widget_builder: 'WidgetBuilder', *args, **kwargs):
        self.select_combo: QComboBox = None
        self.items_group: QGroupBox = None

        super().__init__(schema, ui_schema, widget_builder, *args, **kwargs)

        self.widget_labels: List = []
        self.widgets: List = []
        self.populate_from_schema(schema, ui_schema, widget_builder)

        self.any_of_schemas: List[Schema] = _any_of_schema(schema, widget_builder)

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

        _combo_items = []
        for sub_schema in schema.get('anyOf', []):
            try:  # TODO: Use BBuilderClass to unify the determination
                name = sub_schema['$ref']
                c_name = name.split('/')[-1]
            except KeyError:
                c_name = name = sub_schema['type']

            _combo_items.append(c_name)
            sub_ui_schema = ui_schema.get(name, {})

            widget = widget_builder.create_widget(sub_schema, sub_ui_schema, parent=self)  # TODO onchanged
            self.widget_labels.append(c_name)
            self.widgets.append(widget)
            widget.setVisible(False)

            widget.on_changed.connect(partial(self.widget_on_changed, name))
            if 'title' in schema:
                self.setTitle(schema['title'])

            if 'description' in schema:
                self.setToolTip(schema['description'])

            self.items_group.layout().addWidget(widget)

        self.select_combo.addItems(_combo_items)
        return self.widgets

    def widget_on_changed(self, name: str, value):
        # self.state[name] = value
        self.on_changed.emit(self.state)

    @state_property
    def state(self) -> dict:
        _idx = self.select_combo.currentIndex()
        return self.widgets[_idx].state

    def _matches(self, index: int, state) -> bool:
        """whether `state` conforms to the anyOf-branch with the given index.

        jsonschema does not reject undeclared keys for nested object-branches
        (the ``additionalProperties``-keyword is not enforced reliably), so for
        object-valued states we additionally require every key to be a declared
        property of that branch.
        """
        checker = self.any_of_schemas[index].schema['properties'][CHECKER_KEY]
        if isinstance(state, dict):
            props = checker.get('properties', {})
            if any(key not in props for key in state):
                return False
        return self.any_of_schemas[index].is_valid_data({CHECKER_KEY: state})

    @state.setter
    def state(self, state: dict):
        # A list/tuple of values fills every anyOf-branch with its own default
        # (the function may be called after initializing the form including all
        # defaults for any possible item).
        if isinstance(state, (list, tuple)):
            for idx, _dat in enumerate(state):
                if idx >= len(self.widgets):
                    break
                self.widgets[idx].state = _dat
            return

        # A scalar/dict value selects and fills the matching anyOf-branch.
        for idx in range(len(self.any_of_schemas)):
            if self._matches(idx, state):
                self.widgets[idx].state = state
                self.select_combo.setCurrentIndex(idx)
                return

        # No branch validates the value (e.g. an unconstrained default that does
        # not match any alternative).  Fill the first sub-widget that accepts the
        # value instead of crashing on the fallback-selection.
        for widget in self.widgets:
            try:
                widget.state = state
                return
            except Exception:
                continue

    def show_title(self) -> bool:
        return False
