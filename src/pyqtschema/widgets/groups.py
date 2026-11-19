import logging
from functools import partial
from typing import TYPE_CHECKING, Tuple, Dict

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QCheckBox, QGroupBox, QWidget, QGridLayout, QLabel, QSizePolicy

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property

if TYPE_CHECKING:  # pragma: no cover
    from pyqtschema.builder import WidgetBuilder

logger = logging.getLogger(__name__)


class ObjectSchemaWidget(SchemaWidgetMixin, QGroupBox):

    def __init__(self, schema: dict, ui_schema: dict, widget_builder: 'WidgetBuilder', *args, **kwargs):
        super().__init__(schema, ui_schema, widget_builder, *args, **kwargs)

        self.widgets = self.populate_from_schema(schema, ui_schema, widget_builder)

    @state_property
    def state(self) -> dict:
        return {k: w.state for k, w in self.widgets.items()}

    @state.setter
    def state(self, state: dict):
        # partial states only update the given properties; unknown keys (e.g.
        # data of an older schema-version) are skipped instead of raising.
        for name, value in state.items():
            widget = self.widgets.get(name)
            if widget is None:
                logger.warning("Ignoring unknown property %r for object %r", name, self.schema.get('title', ''))
                continue
            widget.state = value

    def handle_error(self, path: Tuple[str], err: Exception):
        """Route ``err`` to the field at ``path[0]``; an empty path marks the whole object."""
        if not path:
            self._set_valid_state(err)
            return
        name, *tail = path
        widget = self.widgets.get(name)
        if widget is not None:
            widget.handle_error(tuple(tail), err)

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
            _show_title = sub_ui_schema.get('ui:show_title', True)

            widget = widget_builder.create_widget(sub_schema, sub_ui_schema, parent=self)  # TODO onchanged
            widget.on_changed.connect(partial(self.widget_on_changed, name))
            widget.setHidden(_hide)
            widget.setDisabled(_disable)

            _row_index = layout.rowCount()
            _title = sub_schema.get("title", name)
            # boolean fields: put the title on the checkbox itself so the shown
            # label toggles the value and the check-indicator sits directly next
            # to the text (a separate read-only QLabel would not be clickable).
            if isinstance(widget, QCheckBox) and widget.show_title() and _show_title:
                widget.setText(str(_title))
                layout.addWidget(widget, _row_index, 0, 1, 2)
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            elif widget.show_title() and _show_title:
                label = sub_schema.get("title", name)
                _lbl = QLabel(label, parent=self)
                _lbl.setHidden(_hide)
                _lbl.setDisabled(_disable)

                layout.addWidget(_lbl, _row_index, 0)
                layout.addWidget(widget, _row_index, 1)
                widget: QWidget
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

            else:
                layout.addWidget(widget, _row_index, 0, 1, 2)
            widgets[name] = widget

        return widgets
