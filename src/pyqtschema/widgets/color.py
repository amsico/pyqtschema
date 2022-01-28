from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QPushButton, QColorDialog

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property


class QColorButton(QPushButton):
    """Color picker widget QPushButton subclass.

    Implementation derived from https://martinfitzpatrick.name/article/qcolorbutton-a-color-selector-tool-for-pyqt/
    """

    colorChanged = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(QColorButton, self).__init__(*args, **kwargs)

        self._color = None
        self.pressed.connect(self.onColorPicker)

    def color(self):
        return self._color

    def setColor(self, color):
        if color != self._color:
            self._color = color
            self.colorChanged.emit()

        if self._color:
            self.setStyleSheet("background-color: %s;" % self._color)
        else:
            self.setStyleSheet("")

    def onColorPicker(self):
        dlg = QColorDialog(self)
        if self._color:
            dlg.setCurrentColor(QColor(self._color))

        if dlg.exec_():
            self.setColor(dlg.currentColor().name())

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.setColor(None)

        return super(QColorButton, self).mousePressEvent(event)


class ColorSchemaWidget(SchemaWidgetMixin, QColorButton):
    """Widget representation of a string with the 'color' format keyword."""

    def configure(self):
        self.colorChanged.connect(lambda: self.on_changed.emit(self.state))

    @state_property
    def state(self) -> str:
        return self.color()

    @state.setter
    def state(self, data: str):
        self.setColor(data)
