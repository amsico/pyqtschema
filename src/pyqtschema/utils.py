import sys
from enum import Enum
from json import JSONEncoder, dump
from typing import Dict, Any

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


class Encoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Enum):
            return o.value
        return JSONEncoder.default(self, o)


def json_dump(obj, fp, *, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, indent=None,
              separators=None, sort_keys=False, **kwargs):
    """ adjusted json-dump to support Enum-values"""
    kwargs['cls'] = Encoder
    return dump(obj, fp, skipkeys=skipkeys, ensure_ascii=ensure_ascii, check_circular=check_circular,
                allow_nan=allow_nan, indent=indent, separators=separators, sort_keys=sort_keys, **kwargs)
