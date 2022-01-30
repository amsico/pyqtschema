import sys
from typing import Dict

from PyQt5.QtWidgets import QApplication

from pyqtschema.builder import WidgetBuilder


def build_example(schema: Dict):
    app = QApplication(sys.argv)
    builder = WidgetBuilder(schema)
    form = builder.create_form()
    form.show()
    app.exec_()
