from typing import List

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QLabel

from pyqtschema.widgets.base import SchemaWidgetMixin


class FormWidget(QWidget):

    def __init__(self, widget: SchemaWidgetMixin, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.error_widget = QGroupBox(parent=self)
        self.error_widget.setTitle("Errors")
        self.error_layout = QVBoxLayout()
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
            widget = QLabel(f"<b>.{'.'.join(err.path)}</b> {err.message}")
            layout.addWidget(widget)

    def clear_errors(self):
        self.error_widget.hide()
