from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property


class FilepathSchemaWidget(SchemaWidgetMixin, QWidget):

    def __init__(self, schema: dict, ui_schema: dict, widget_builder: 'WidgetBuilder'):
        super().__init__(schema, ui_schema, widget_builder)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.path_widget = QLineEdit()
        self.button_widget = QPushButton("Browse")
        layout.addWidget(self.path_widget)
        layout.addWidget(self.button_widget)

        self.button_widget.clicked.connect(self._on_clicked)
        self.path_widget.textChanged.connect(self.on_changed.emit)

    def _on_clicked(self, flag):
        path, filter = QFileDialog.getOpenFileName()
        self.path_widget.setText(path)

    @state_property
    def state(self) -> str:
        return self.path_widget.text()

    @state.setter
    def state(self, state: str):
        self.path_widget.setText(state)


class DirectorypathSchemaWidget(FilepathSchemaWidget):
    def _on_clicked(self, flag):
        path = QFileDialog.getExistingDirectory()
        self.path_widget.setText(path)
