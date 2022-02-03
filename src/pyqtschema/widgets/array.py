from functools import partial
from typing import List, Tuple, Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStyle, QGroupBox

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property
from pyqtschema.widgets.utils import iter_layout_widgets, is_concrete_schema


class ArrayControlsWidget(QWidget):
    on_delete = pyqtSignal()
    on_move_up = pyqtSignal()
    on_move_down = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        style = self.style()

        self.up_button = QPushButton()
        self.up_button.setIcon(style.standardIcon(QStyle.SP_ArrowUp))
        self.up_button.clicked.connect(lambda _: self.on_move_up.emit())

        self.delete_button = QPushButton()
        self.delete_button.setIcon(style.standardIcon(QStyle.SP_DialogCancelButton))
        self.delete_button.clicked.connect(lambda _: self.on_delete.emit())

        self.down_button = QPushButton()
        self.down_button.setIcon(style.standardIcon(QStyle.SP_ArrowDown))
        self.down_button.clicked.connect(lambda _: self.on_move_down.emit())

        group_layout = QHBoxLayout()
        self.setLayout(group_layout)
        group_layout.addWidget(self.up_button)
        group_layout.addWidget(self.down_button)
        group_layout.addWidget(self.delete_button)
        group_layout.setSpacing(0)
        group_layout.addStretch(0)


class ArrayRowWidget(QWidget):

    def __init__(self, widget: QWidget, controls: ArrayControlsWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QHBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(controls)
        self.setLayout(layout)

        self.widget = widget
        self.controls = controls


class ArraySchemaWidget(SchemaWidgetMixin, QGroupBox):

    def show_title(self) -> bool:
        return False

    @property
    def rows(self) -> List[ArrayRowWidget]:
        return [*iter_layout_widgets(self.array_layout)]

    @state_property
    def state(self) -> list:
        return [r.widget.state for r in self.rows]

    @state.setter
    def state(self, state: list):
        for row in self.rows:
            self._remove_item(row)

        for item in state:
            self._add_item(item)

        self.on_changed.emit(self.state)

    def handle_error(self, path: Tuple[str], err: Exception):
        index, *tail = path
        self.rows[index].widget.handle_error(tail, err)

    def configure(self):
        layout = QVBoxLayout()
        style = self.style()

        if 'title' in self.schema:
            self.setTitle(self.schema['title'])

        self.add_button = QPushButton()
        self.add_button.setIcon(style.standardIcon(QStyle.SP_DialogOkButton))
        self.add_button.clicked.connect(lambda _: self.add_item())

        self.array_layout = QVBoxLayout()
        # self.array_layout.setContentsMargins(0, 0, 0, 0)
        array_widget = QWidget(self)
        array_widget.setLayout(self.array_layout)

        self.on_changed.connect(self._on_updated)

        layout.addWidget(self.add_button)
        layout.addWidget(array_widget)
        self.setLayout(layout)

    def _on_updated(self, state):
        # Update add button
        disabled = self.next_item_schema is None
        self.add_button.setEnabled(not disabled)

        previous_row = None
        for i, row in enumerate(self.rows):
            if previous_row:
                can_exchange_previous = previous_row.widget.schema == row.widget.schema
                row.controls.up_button.setEnabled(can_exchange_previous)
                previous_row.controls.down_button.setEnabled(can_exchange_previous)
            else:
                row.controls.up_button.setEnabled(False)
            row.controls.delete_button.setEnabled(not self.is_fixed_schema(i))
            previous_row = row

        if previous_row:
            previous_row.controls.down_button.setEnabled(False)

    def is_fixed_schema(self, index: int) -> bool:
        schema = self.schema['items']
        if isinstance(schema, dict):
            return False

        return index < len(schema)

    @property
    def next_item_schema(self) -> Optional[dict]:
        item_schema = self.schema['items']

        if isinstance(item_schema, dict):
            return item_schema

        index = len(self.rows)

        try:
            item_schema = item_schema[index]
        except IndexError:
            item_schema = self.schema.get("additionalItems", {})
            if isinstance(item_schema, bool):
                return None

        if not is_concrete_schema(item_schema):
            return None

        return item_schema

    def add_item(self, item_state=None):
        self._add_item(item_state)
        self.on_changed.emit(self.state)

    def remove_item(self, row: ArrayRowWidget):
        self._remove_item(row)
        self.on_changed.emit(self.state)

    def move_item_up(self, row: ArrayRowWidget):
        index = self.rows.index(row)
        self.array_layout.insertWidget(max(0, index - 1), row)
        self.on_changed.emit(self.state)

    def move_item_down(self, row: ArrayRowWidget):
        index = self.rows.index(row)
        self.array_layout.insertWidget(min(len(self.rows) - 1, index + 1), row)
        self.on_changed.emit(self.state)

    def _add_item(self, item_state=None):
        item_schema = self.next_item_schema

        # Create widget
        item_ui_schema = self.ui_schema.get("items", {})
        widget = self.widget_builder.create_widget(item_schema, item_ui_schema, item_state, parent=self)
        controls = ArrayControlsWidget()

        # Create row
        row = ArrayRowWidget(widget, controls)
        row.layout().setContentsMargins(0, 0, 0, 0)

        self.array_layout.addWidget(row)

        # Setup callbacks
        widget.on_changed.connect(partial(self.widget_on_changed, row))
        controls.on_delete.connect(partial(self.remove_item, row))
        controls.on_move_up.connect(partial(self.move_item_up, row))
        controls.on_move_down.connect(partial(self.move_item_down, row))

        return row

    def _remove_item(self, row: ArrayRowWidget):
        self.array_layout.removeWidget(row)
        row.deleteLater()

    def widget_on_changed(self, row: ArrayRowWidget, value):
        self.state[self.rows.index(row)] = value
        self.on_changed.emit(self.state)
