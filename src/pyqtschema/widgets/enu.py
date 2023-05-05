from enum import Enum

from qtpy.QtWidgets import QComboBox

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property


class EnumSchemaWidget(SchemaWidgetMixin, QComboBox):

    @state_property
    def state(self):
        return self.itemData(self.currentIndex())

    @state.setter
    def state(self, value):
        val = value
        if isinstance(val, Enum):
            val = val.value
        index = self.findData(val)
        if index == -1:
            raise ValueError(val)
        self.setCurrentIndex(index)

    def configure(self):
        options = self.schema["enum"]
        for idx, opt in enumerate(options):
            vis, val = str(opt), opt
            self.addItem(vis)
            self.setItemData(idx, val)

        self.currentIndexChanged.connect(lambda _: self.on_changed.emit(self.state))

    def _index_changed(self, index: int):
        self.on_changed.emit(self.state)
