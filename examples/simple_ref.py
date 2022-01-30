import sys

from PyQt5.QtWidgets import QApplication
from pydantic import BaseModel, Field

from pyqtschema.builder import WidgetBuilder


class UnitValue(BaseModel):
    value: float
    unit: str


class Limits(BaseModel):
    name: str = Field(default='dummy', description='stored in name-column')
    upper: UnitValue
    lower: UnitValue


if __name__ == '__main__':
    app = QApplication(sys.argv)
    builder = WidgetBuilder(Limits.schema())
    form = builder.create_form()
    form.show()

    app.exec_()
