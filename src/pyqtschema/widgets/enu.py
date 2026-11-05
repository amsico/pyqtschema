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

    def _options(self):
        """list of ``(value, display-label)`` for this enum.

        * ``enum`` (values): the value itself is the label (original
          pyqtschema behaviour).
        * ``oneOf`` with per-alternative ``const`` + ``title``: the
          standard-compliant way to label enum-options, recommended by
          json-schema-spec#57:
          https://github.com/json-schema-org/json-schema-spec/issues/57
        """
        if "enum" in self.schema:
            return [(opt, str(opt)) for opt in self.schema["enum"]]
        if isinstance(self.schema.get("oneOf"), list):
            out = []
            for alt in self.schema["oneOf"]:
                if isinstance(alt, dict) and "const" in alt:
                    value = alt["const"]
                    out.append((value, str(alt.get("title", value))))
            return out
        return []

    def configure(self):
        for value, label in self._options():
            self.addItem(str(label or value))
            self.setItemData(self.count() - 1, value)

        self.currentIndexChanged.connect(lambda _: self.on_changed.emit(self.state))

    def _index_changed(self, index: int):
        self.on_changed.emit(self.state)
