import sys
from typing import Dict

from PyQt5.QtWidgets import QApplication, QScrollArea, QWidget

from pyqtschema.builder import WidgetBuilder


def build_example_widget(schema: Dict, ui_schema=None) -> QWidget:
    builder = WidgetBuilder(schema)
    form = builder.create_form(ui_schema=ui_schema)
    return form


def build_example(schema: Dict, scrollbar: bool = True):
    app = QApplication(sys.argv)
    widget = form = build_example_widget(schema)
    if scrollbar:
        widget = QScrollArea()
        widget.setWidget(form)
        widget.setWidgetResizable(True)

    widget.show()
    app.exec_()
