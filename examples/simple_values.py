import sys

from PyQt5.QtWidgets import QApplication
from pydantic import BaseModel, Field

from pyqtschema.builder import WidgetBuilder


class Simple(BaseModel):
    string: str = Field()
    boolean: bool = Field(default=True)
    integer: int = Field(default=2)
    number: float = Field(default=2.2)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    builder = WidgetBuilder(Simple.schema())
    form = builder.create_form()
    form.show()

    app.exec_()
