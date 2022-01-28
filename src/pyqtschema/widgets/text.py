from PyQt5.QtWidgets import QLineEdit, QTextEdit

from .base import SchemaWidgetMixin, state_property


class TextSchemaWidget(SchemaWidgetMixin, QLineEdit):
    """ """

    def configure(self):
        self.textChanged.connect(self.on_changed.emit)

    @state_property
    def state(self) -> str:
        return str(self.text())

    @state.setter
    def state(self, state: str):
        self.setText(state)


class TextAreaSchemaWidget(SchemaWidgetMixin, QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @state_property
    def state(self) -> str:
        return str(self.toPlainText())

    @state.setter
    def state(self, state: str):
        self.setPlainText(state)

    def configure(self):
        self.textChanged.connect(lambda: self.on_changed.emit(self.state))


class PasswordWidget(TextSchemaWidget):

    def configure(self):
        super().configure()

        self.setEchoMode(self.Password)
