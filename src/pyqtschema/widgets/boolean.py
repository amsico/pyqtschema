from PyQt5.QtWidgets import QCheckBox

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property


class CheckboxSchemaWidget(SchemaWidgetMixin, QCheckBox):

    @state_property
    def state(self) -> bool:
        return self.isChecked()

    @state.setter
    def state(self, checked: bool):
        self.setChecked(checked)

    def configure(self):
        self.stateChanged.connect(lambda _: self.on_changed.emit(self.state))
