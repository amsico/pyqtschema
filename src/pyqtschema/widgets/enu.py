from PyQt5.QtWidgets import QComboBox

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property


class EnumSchemaWidget(SchemaWidgetMixin, QComboBox):

    @state_property
    def state(self):
        return self.itemData(self.currentIndex())

    @state.setter
    def state(self, value):
        index = self.findData(value)
        if index == -1:
            raise ValueError(value)
        self.setCurrentIndex(index)

    def configure(self):
        options = self.schema["enum"]
        for i, opt in enumerate(options):
            self.addItem(str(opt))
            self.setItemData(i, opt)

        self.currentIndexChanged.connect(lambda _: self.on_changed.emit(self.state))

    def _index_changed(self, index: int):
        self.on_changed.emit(self.state)
