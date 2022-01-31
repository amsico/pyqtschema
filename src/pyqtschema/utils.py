import sys
from typing import Dict

from PyQt5.QtWidgets import QApplication, QScrollArea

from pyqtschema.builder import WidgetBuilder


def build_example(schema: Dict, scrollbar: bool = True):
    app = QApplication(sys.argv)
    builder = WidgetBuilder(schema)
    widget = form = builder.create_form()
    if scrollbar:
        widget = QScrollArea()
        widget.setWidget(form)
        widget.setWidgetResizable(True)

    widget.show()
    app.exec_()
